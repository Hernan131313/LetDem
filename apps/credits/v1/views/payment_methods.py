from commons.paginators import CustomPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.models import PaymentMethod
from credits.v1.serializers import payment_methods


class ListCreatePaymentMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'payment_methods', PaymentMethod.objects.none()).all()
        queryset = queryset.order_by('-is_default')
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = payment_methods.PaymentMethodSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)

    def post(self, request, *args, **kwargs):
        serializer = payment_methods.CreatePaymentMethodSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serialized_data = payment_methods.PaymentMethodSerializer(instance).data
        return Response(data=serialized_data, status=status.HTTP_201_CREATED)


class DeletePaymentMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, uuid, *args, **kwargs):
        user = request.user
        _payment_methods = getattr(user, 'payment_methods', PaymentMethod.objects.none()).all()
        payment_method: PaymentMethod = _payment_methods.filter(uuid=uuid).last()

        if not payment_method:
            return Response(data={'message': 'Payment Method Not Found'}, status=status.HTTP_404_NOT_FOUND)

        if payment_method.is_default:
            if _payment_method := PaymentMethod.objects.exclude(id=payment_method.id).last():
                _payment_method.mark_as_default()

        payment_method.delete()
        return Response(data={'message': 'Payment Method Deleted'}, status=status.HTTP_204_NO_CONTENT)


class MarkAsDefaultPaymentMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, uuid, *args, **kwargs):
        user = request.user
        _payment_methods = getattr(user, 'payment_methods', PaymentMethod.objects.none()).all()
        payment_method: PaymentMethod = _payment_methods.filter(uuid=uuid).last()
        if not payment_method:
            return Response(data={'message': 'Payment Method Not Found'}, status=status.HTTP_404_NOT_FOUND)

        payment_method.mark_as_default()
        return Response(data={'message': 'Payment Marked As Default'}, status=status.HTTP_200_OK)
