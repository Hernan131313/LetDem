from commons.paginators import CustomPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.models import Withdraw
from credits.v1.serializers import withdrawals


class ListCreateWithdrawalAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        paginator = self.pagination_class()
        if not request.user.has_earning_account:
            queryset = Withdraw.objects.none()
        else:
            queryset = getattr(request.user.earning_account, 'withdrawals', Withdraw.objects.none()).all()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = withdrawals.ListWithdrawalSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)

    def post(self, request, *args, **kwargs):
        serializer = withdrawals.CreateWithdrawalSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Withdrawal Created'}, status=status.HTTP_201_CREATED)
