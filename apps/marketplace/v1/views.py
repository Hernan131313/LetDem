import secrets
import string
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.models import EarningAccount
from credits.providers.stripe.utils import create_marketplace_payment_intent
from marketplace.forms import CategoryForm, StoreForm, ProductForm
from marketplace.models import Category, Store, Product, Voucher, Order, OrderItem
from marketplace.v1.serializers import (
    CategorySerializer,
    StoreSerializer,
    StoreAdminSerializer,
    ProductSerializer,
    ProductAdminSerializer,
    VoucherSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    CreateVoucherSerializer,
    ValidateVoucherSerializer,
)


class CategoryListView(generics.ListAPIView):
    """Lista todas las categorías disponibles"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class StoreListView(generics.ListAPIView):
    """Lista todas las tiendas activas"""
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category__name=category)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class StoreDetailView(generics.RetrieveAPIView):
    """Detalle de una tienda específica"""
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer


class ProductListView(generics.ListAPIView):
    """Lista todos los productos activos"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        store_id = self.request.query_params.get('store', None)
        search = self.request.query_params.get('search', None)
        
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """Detalle de un producto específico"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer


class VoucherListView(generics.ListAPIView):
    """Lista los vouchers del usuario autenticado"""
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo los vouchers del usuario actual"""
        user = self.request.user
        queryset = Voucher.objects.filter(user=user).select_related(
            'product', 'store', 'store__category'
        )
        
        # Filtros opcionales
        status_filter = self.request.query_params.get('status') if hasattr(self.request, 'query_params') else self.request.GET.get('status')
        redeem_type = self.request.query_params.get('redeem_type') if hasattr(self.request, 'query_params') else self.request.GET.get('redeem_type')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        
        if redeem_type:
            queryset = queryset.filter(redeem_type=redeem_type.upper())
        
        return queryset


class VoucherDetailView(generics.RetrieveAPIView):
    """Detalle de un voucher específico"""
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Solo puede ver sus propios vouchers"""
        return Voucher.objects.filter(user=self.request.user).select_related(
            'product', 'store', 'store__category'
        )


class PendingVouchersView(generics.ListAPIView):
    """List pending vouchers for the authenticated user."""

    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Voucher.objects.filter(user=self.request.user, status=Voucher.Status.PENDING)
            .select_related('product', 'store', 'store__category')
            .order_by('-created')
        )


class OrdersView(APIView):
    """Expose order history (GET) and order creation (POST)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders_qs = (
            Order.objects.filter(user=request.user)
            .prefetch_related('items', 'items__product')
            .order_by('-created')
        )
        orders = list(orders_qs)
        serializer = OrderSerializer(orders, many=True)
        stats = self._build_stats(request.user, orders)
        return Response({'stats': stats, 'orders': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _build_stats(user, orders):
        total_orders = len(orders)
        total_spent = sum((order.total for order in orders), Decimal('0'))
        total_saved = sum((order.points_discount for order in orders), Decimal('0'))
        total_points_used = sum(order.points_used_amount for order in orders)
        return {
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'total_points_used': int(total_points_used),
            'total_saved': float(total_saved),
            'current_points': user.total_points,
        }

class CreateVoucherOnlineView(APIView):
    """Create a virtual card (voucher) without scanning QR codes."""

    permission_classes = [IsAuthenticated]
    CARD_VALIDITY = {
        Voucher.RedeemType.ONLINE: timedelta(hours=48),
        Voucher.RedeemType.IN_STORE: timedelta(minutes=5),
    }
    
    def post(self, request):
        user = self._resolve_user(request)
        serializer = CreateVoucherSerializer(
            data=request.data,
            context={'request': request, 'user': user},
        )
        
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        if not isinstance(validated_data, dict) or not validated_data:
            raise ValidationError({'detail': 'No valid data provided'})
        
        user = validated_data.get('user')
        product = validated_data.get('product')
        redeem_type = validated_data.get('redeem_type')
        
        if not user or not product or not redeem_type:
            raise ValidationError({'detail': 'Missing required fields: user, product, or redeem_type'})
        expires_at = timezone.now() + self.CARD_VALIDITY.get(
            redeem_type,
            timedelta(hours=48),
        )
        
        try:
            with transaction.atomic():
                # Verificar nuevamente el saldo de puntos
                if user.total_points < 500:
                    return Response(
                        {'error': 'No tienes suficientes puntos'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                voucher = Voucher.objects.create(
                    user=user,
                    product=product,
                    store=product.store,
                    code=self._generate_voucher_code(),
                    redeem_type=redeem_type,
                    discount_percentage=30,
                    points_used=500,
                    expires_at=expires_at,
                    status=Voucher.Status.PENDING,
                )
                
                user.total_points -= 500
                user.save(update_fields=['total_points'])
                
                response_serializer = VoucherSerializer(voucher)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response(
                {'error': f'Error al crear tarjeta virtual: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _resolve_user(self, request):
        if not request.user.is_authenticated:
            raise ValidationError({'user': 'Authentication required to create vouchers'})
        return request.user
    
    def _generate_voucher_code(self):
        """Genera un código único para la tarjeta/voucher"""
        while True:
            random_part = ''.join(
                secrets.choice(string.digits) for _ in range(5)
            )
            code = f'LETDEM-{random_part}'
            if not Voucher.objects.filter(code=code).exists():
                return code


class ValidateVoucherView(APIView):
    """Validar y marcar un voucher como usado"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ValidateVoucherSerializer(data=request.data)
        # Raise a proper DRF ValidationError if data is invalid so validated_data is guaranteed.
        serializer.is_valid(raise_exception=True)
        
        validated = getattr(serializer, 'validated_data', None)
        if validated is None:
            raise ValidationError({'code': 'Invalid or missing data'})
        
        code = validated.get('code')
        
        try:
            with transaction.atomic():
                # Buscar voucher
                voucher = Voucher.objects.select_related(
                    'user', 'product', 'store'
                ).get(code=code)
                
                # Validar que no haya expirado
                if voucher.is_expired:
                    return Response(
                        {
                            'error': 'El voucher ha expirado',
                            'expired_at': voucher.expires_at
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validar que no esté ya usado
                if voucher.status == Voucher.Status.REDEEMED:
                    return Response(
                        {
                            'error': 'El voucher ya ha sido usado',
                            'redeemed_at': voucher.redeemed_at
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validar que esté pendiente
                if voucher.status != Voucher.Status.PENDING:
                    return Response(
                        {'error': f'El voucher tiene estado: {voucher.status}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Marcar como canjeado
                voucher.status = Voucher.Status.REDEEMED
                voucher.redeemed_at = timezone.now()
                voucher.save(update_fields=['status', 'redeemed_at'])
                
                # Serializar y retornar
                response_serializer = VoucherSerializer(voucher)
                return Response(
                    {
                        'message': 'Voucher validado exitosamente',
                        'voucher': response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        
        except Voucher.DoesNotExist:
            return Response(
                {'error': 'Voucher no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error al validar voucher: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PurchaseWithRedeemView(APIView):
    """Procesar compra con canje de puntos (30% descuento) usando wallet + Stripe"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        payment_intent_id = request.data.get('payment_intent_id')  # Si ya se pagó con Stripe
        
        if not product_id:
            return Response(
                {'error': 'product_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'La cantidad debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Cantidad inválida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required to purchase'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Verificar puntos
            if user.total_points < 500:
                return Response(
                    {'error': f'No tienes suficientes puntos. Tienes {user.total_points}, necesitas 500'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener producto
            product = Product.objects.select_related('store').get(
                id=product_id,
                is_active=True
            )
            
            # Verificar stock
            if product.stock < quantity:
                return Response(
                    {'error': f'Stock insuficiente. Disponibles: {product.stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular precios (en euros)
            unit_price = float(product.final_price)
            subtotal = unit_price * quantity
            discount_30_percent = subtotal * 0.30
            total = subtotal - discount_30_percent
            total_cents = int(total * 100)  # Convertir a centavos
            
            # Obtener wallet del usuario
            wallet_balance_cents = 0
            earning_account = None
            try:
                earning_account = EarningAccount.objects.get(user=user)
                wallet_balance_cents = earning_account.available_balance
            except EarningAccount.DoesNotExist:
                pass
            
            # Calcular cuánto usar de wallet y cuánto de Stripe
            amount_from_wallet_cents = min(wallet_balance_cents, total_cents)
            amount_from_stripe_cents = total_cents - amount_from_wallet_cents
            
            # Si necesita pagar con Stripe y no se ha pagado aún
            if amount_from_stripe_cents > 0 and not payment_intent_id:
                # Verificar que el usuario tenga customer_id de Stripe
                if not user.provider_customer_id:
                    return Response(
                        {'error': 'Debes configurar un método de pago primero'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Crear PaymentIntent
                payment_intent = create_marketplace_payment_intent(
                    user=user,
                    amount=amount_from_stripe_cents,
                    currency='eur'
                )
                
                return Response({
                    'requires_payment': True,
                    'client_secret': payment_intent.client_secret,
                    'payment_breakdown': {
                        'total': float(total),
                        'total_cents': total_cents,
                        'from_wallet': amount_from_wallet_cents / 100,
                        'from_wallet_cents': amount_from_wallet_cents,
                        'from_stripe': amount_from_stripe_cents / 100,
                        'from_stripe_cents': amount_from_stripe_cents,
                    }
                }, status=status.HTTP_200_OK)
            
            # Procesar compra (ya se pagó o todo es de wallet)
            with transaction.atomic():
                # Crear orden
                order = Order.objects.create(
                    user=user,
                    status=Order.Status.PAID,
                    subtotal=subtotal,
                    points_discount=discount_30_percent,
                    total=total,
                    used_points=True,
                    points_used_amount=500
                )
                
                # Crear item de orden
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
                
                # Descontar de wallet si se usó
                if amount_from_wallet_cents > 0 and earning_account is not None:
                    earning_account.available_balance -= amount_from_wallet_cents
                    earning_account.balance -= amount_from_wallet_cents
                    earning_account.save(update_fields=['available_balance', 'balance'])
                
                # Descontar puntos
                user.total_points -= 500
                user.save(update_fields=['total_points'])
                
                # Actualizar stock
                product.stock -= quantity
                product.save(update_fields=['stock'])
                
                return Response({
                    'message': 'Compra realizada exitosamente',
                    'order': {
                        'id': str(order.pk),
                        'subtotal': float(order.subtotal),
                        'discount': float(order.points_discount),
                        'total': float(order.total),
                        'points_used': order.points_used_amount,
                        'remaining_points': user.total_points,
                        'payment_breakdown': {
                            'from_wallet': amount_from_wallet_cents / 100,
                            'from_stripe': amount_from_stripe_cents / 100,
                        }
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error al procesar compra: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PurchaseWithoutRedeemView(APIView):
    """Procesar compra sin canje de puntos (precio normal) usando wallet + Stripe"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        payment_intent_id = request.data.get('payment_intent_id')  # Si ya se pagó con Stripe
        
        if not product_id:
            return Response(
                {'error': 'product_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'La cantidad debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Cantidad inválida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required to purchase'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Obtener producto
            product = Product.objects.select_related('store').get(
                id=product_id,
                is_active=True
            )
            
            # Verificar stock
            if product.stock < quantity:
                return Response(
                    {'error': f'Stock insuficiente. Disponibles: {product.stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular precios (en euros)
            unit_price = float(product.final_price)
            subtotal = unit_price * quantity
            total = subtotal  # Sin descuento
            total_cents = int(total * 100)  # Convertir a centavos
            
            # Obtener wallet del usuario
            wallet_balance_cents = 0
            try:
                earning_account = user.earning_account
                wallet_balance_cents = earning_account.available_balance
            except EarningAccount.DoesNotExist:
                pass
            
            # Calcular cuánto usar de wallet y cuánto de Stripe
            amount_from_wallet_cents = min(wallet_balance_cents, total_cents)
            amount_from_stripe_cents = total_cents - amount_from_wallet_cents
            
            # Si necesita pagar con Stripe y no se ha pagado aún
            if amount_from_stripe_cents > 0 and not payment_intent_id:
                # Verificar que el usuario tenga customer_id de Stripe
                if not user.provider_customer_id:
                    return Response(
                        {'error': 'Debes configurar un método de pago primero'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Crear PaymentIntent
                payment_intent = create_marketplace_payment_intent(
                    user=user,
                    amount=amount_from_stripe_cents,
                    currency='eur'
                )
                
                return Response({
                    'requires_payment': True,
                    'client_secret': payment_intent.client_secret,
                    'payment_breakdown': {
                        'total': float(total),
                        'total_cents': total_cents,
                        'from_wallet': amount_from_wallet_cents / 100,
                        'from_wallet_cents': amount_from_wallet_cents,
                        'from_stripe': amount_from_stripe_cents / 100,
                        'from_stripe_cents': amount_from_stripe_cents,
                    }
                }, status=status.HTTP_200_OK)
            
            # Procesar compra (ya se pagó o todo es de wallet)
            with transaction.atomic():
                # Crear orden
                order = Order.objects.create(
                    user=user,
                    status=Order.Status.PAID,
                    subtotal=subtotal,
                    points_discount=0,
                    total=total,
                    used_points=False,
                    points_used_amount=0
                )
                
                # Crear item de orden
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
                
                # Descontar de wallet si se usó
                if amount_from_wallet_cents > 0:
                    earning_account.available_balance -= amount_from_wallet_cents
                    earning_account.balance -= amount_from_wallet_cents
                    earning_account.save(update_fields=['available_balance', 'balance'])
                
                # Actualizar stock
                product.stock -= quantity
                product.save(update_fields=['stock'])
                
                return Response({
                    'message': 'Compra realizada exitosamente',
                    'order': {
                        'id': str(order.id),
                        'subtotal': float(order.subtotal),
                        'total': float(order.total),
                        'payment_breakdown': {
                            'from_wallet': amount_from_wallet_cents / 100,
                            'from_stripe': amount_from_stripe_cents / 100,
                        }
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error al procesar compra: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryAdminCreateView(generics.CreateAPIView):
    """Permite crear categorías del marketplace mediante POST."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class StoreAdminCreateView(generics.CreateAPIView):
    """Permite crear tiendas del marketplace mediante POST."""
    queryset = Store.objects.all()
    serializer_class = StoreAdminSerializer
    permission_classes = [IsAdminUser]


class ProductAdminCreateView(generics.CreateAPIView):
    """Permite crear productos del marketplace mediante POST."""
    queryset = Product.objects.all()
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdminUser]


class MarketplaceAdminPanelView(TemplateView):
    """
    Panel HTML sencillo para gestionar categorías, tiendas y productos sin usar el admin clásico.
    No requiere autenticación (según solicitud del usuario).
    """
    template_name = 'marketplace/admin_panel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_form'] = kwargs.get('category_form') or CategoryForm()
        context['store_form'] = kwargs.get('store_form') or StoreForm()
        context['product_form'] = kwargs.get('product_form') or ProductForm()
        context['categories'] = Category.objects.order_by('-created')[:20]
        context['stores'] = Store.objects.select_related('category').order_by('-created')[:20]
        context['products'] = Product.objects.select_related('store').order_by('-created')[:20]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'create_category':
            category_form = CategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                messages.success(request, 'Categoría creada correctamente.')
                return redirect('marketplace-admin-panel')
            return self.render_to_response(self.get_context_data(category_form=category_form))

        if action == 'create_store':
            store_form = StoreForm(request.POST)
            if store_form.is_valid():
                store_form.save()
                messages.success(request, 'Tienda creada correctamente.')
                return redirect('marketplace-admin-panel')
            return self.render_to_response(self.get_context_data(store_form=store_form))

        if action == 'create_product':
            product_form = ProductForm(request.POST)
            if product_form.is_valid():
                product_form.save()
                messages.success(request, 'Producto creado correctamente.')
                return redirect('marketplace-admin-panel')
            return self.render_to_response(self.get_context_data(product_form=product_form))

        messages.error(request, 'Acción no reconocida.')
        return redirect('marketplace-admin-panel')

