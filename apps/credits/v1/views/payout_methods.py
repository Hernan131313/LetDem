from commons.paginators import CustomPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.models import PayoutMethod
from credits.v1.serializers import payout_methods


class ListCreatePayoutMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        paginator = self.pagination_class()
        queryset = PayoutMethod.objects.none()
        if request.user.has_earning_account:
            queryset = getattr(request.user.earning_account, 'payout_methods', queryset).all()

        queryset = queryset.order_by('-is_default')
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = payout_methods.ListPayoutMethodSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)

    def post(self, request, *args, **kwargs):
        serializer = payout_methods.CreatePayoutMethodSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Payout Method Created'}, status=status.HTTP_201_CREATED)


class DeletePayoutMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, uuid, *args, **kwargs):
        queryset = PayoutMethod.objects.none()
        if request.user.has_earning_account:
            queryset = getattr(request.user.earning_account, 'payout_methods', queryset).all()
        if payout := queryset.filter(uuid=uuid).last():
            payout.delete()
        return Response(data={'message': 'Payout Method Deleted'}, status=status.HTTP_204_NO_CONTENT)
