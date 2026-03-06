from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.exceptions.types.marketplace import (
    EmptyCart,
    InsufficientPoints,
    InsufficientStock,
    ProductNotFound,
)
from marketplace.models import Category, Store, Product, Order, OrderItem, Voucher


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'display_name', 'icon']


class StoreSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Store
        fields = [
            'id',
            'name',
            'description',
            'category',
            'image_url',
            'latitude',
            'longitude',
            'address',
            'phone',
            'is_open',
            'opening_hours',
            'rating',
            'review_count',
            'is_active',
        ]


class StoreAdminSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )

    class Meta:
        model = Store
        fields = [
            'id',
            'name',
            'description',
            'category',
            'category_id',
            'image_url',
            'latitude',
            'longitude',
            'address',
            'phone',
            'is_open',
            'opening_hours',
            'rating',
            'review_count',
            'is_active',
        ]


class ProductSerializer(serializers.ModelSerializer):
    store_id = serializers.UUIDField(source='store.id', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image_url',
            'price',
            'discount',
            'final_price',
            'stock',
            'rating',
            'review_count',
            'store_id',
            'store_name',
        ]


class ProductAdminSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    store_id = serializers.PrimaryKeyRelatedField(
        queryset=Store.objects.all(),
        source='store',
        write_only=True,
    )
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image_url',
            'price',
            'discount',
            'final_price',
            'stock',
            'rating',
            'review_count',
            'is_active',
            'store',
            'store_id',
        ]

    def get_final_price(self, obj):
        return obj.final_price


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    created_at = serializers.DateTimeField(source='created', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'user_email',
            'status',
            'subtotal',
            'points_discount',
            'total',
            'used_points',
            'points_used_amount',
            'items',
            'created_at',
        ]
        read_only_fields = ['user', 'status', 'created_at']


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer that encapsulates the logic required to build an order and its
    items. Keeping the logic here ensures the API view stays small and that
    responses are serialized consistently.
    """

    items = OrderItemInputSerializer(many=True)
    use_points = serializers.BooleanField(default=False)

    def validate(self, attrs):
        items = attrs.get('items') or []
        if not items:
            raise EmptyCart()

        product_ids = {item['product_id'] for item in items}
        products = (
            Product.objects.filter(id__in=product_ids, is_active=True)
            .select_related('store')
        )
        if products.count() != len(product_ids):
            raise ProductNotFound()

        products_by_id = {str(product.id): product for product in products}
        resolved_items = []
        for payload in items:
            product = products_by_id.get(str(payload['product_id']))
            if product is None:
                raise ProductNotFound()
            if product.stock < payload['quantity']:
                raise InsufficientStock()
            resolved_items.append((product, payload['quantity']))

        attrs['resolved_items'] = resolved_items
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        resolved_items = validated_data['resolved_items']
        use_points = validated_data.get('use_points', False)

        subtotal = Decimal('0')
        for product, quantity in resolved_items:
            subtotal += Decimal(str(product.final_price)) * quantity

        points_discount = Decimal('0')
        points_used = 0
        if use_points:
            if user.total_points < 500:
                raise InsufficientPoints()
            points_discount = (subtotal * Decimal('0.30')).quantize(Decimal('0.01'))
            points_used = 500

        total = (subtotal - points_discount).quantize(Decimal('0.01'))

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                status=Order.Status.PAID,
                subtotal=subtotal,
                points_discount=points_discount,
                total=total,
                used_points=use_points,
                points_used_amount=points_used,
            )

            for product, quantity in resolved_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=Decimal(str(product.final_price)),
                )
                product.stock -= quantity
                product.save(update_fields=['stock'])

            if points_used:
                user.total_points -= points_used
                user.save(update_fields=['total_points'])

        return order


class UserPointsSerializer(serializers.Serializer):
    total_points = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(read_only=True)


class VoucherSerializer(serializers.ModelSerializer):
    """Read serializer for vouchers."""

    user_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.final_price',
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_category = serializers.CharField(source='store.category.display_name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    discount_amount = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    hours_until_expiration = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = [
            'id',
            'code',
            'qr_code',
            'redeem_type',
            'status',
            'discount_percentage',
            'points_used',
            'expires_at',
            'redeemed_at',
            'user',
            'user_email',
            'product',
            'product_name',
            'product_price',
            'store',
            'store_name',
            'store_category',
            'scanned_code',
            'is_valid',
            'is_expired',
            'discount_amount',
            'final_price',
            'hours_until_expiration',
            'created',
            'modified',
        ]
        read_only_fields = [
            'code',
            'qr_code',
            'user',
            'status',
            'redeemed_at',
            'created',
            'modified',
        ]

    def get_discount_amount(self, obj):
        return float(obj.product.final_price) * (float(obj.discount_percentage) / 100)

    def get_final_price(self, obj):
        discount = self.get_discount_amount(obj)
        return float(obj.product.final_price) - discount

    def get_hours_until_expiration(self, obj):
        delta = obj.expires_at - timezone.now()
        hours = delta.total_seconds() / 3600
        return max(hours, 0)


class CreateVoucherSerializer(serializers.Serializer):
    """Serializer used to issue a voucher (virtual card)."""

    product_id = serializers.UUIDField(required=True)
    redeem_type = serializers.ChoiceField(
        choices=Voucher.RedeemType.choices,
        default=Voucher.RedeemType.ONLINE,
    )

    def validate(self, data):
        user = self.context.get('user') or self.context['request'].user
        if user.total_points < 500:
            raise InsufficientPoints()

        try:
            product = Product.objects.select_related('store').get(
                id=data['product_id'],
                is_active=True,
            )
        except Product.DoesNotExist:
            raise ProductNotFound()

        data['product'] = product
        data['user'] = user
        return data


class ValidateVoucherSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, max_length=50)
    pin = serializers.CharField(
        required=False,
        max_length=10,
        help_text=_('Merchant PIN (optional)'),
    )
