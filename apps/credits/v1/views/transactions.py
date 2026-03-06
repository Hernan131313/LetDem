from datetime import timedelta

from commons.paginators import CustomPagination
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from credits.models import Transaction
from credits.v1.serializers import transactions


class ListTransactionsAPIView(APIView):
    """
    API View to list transactions:
    - `?start_date=2024-03-02&end_date=2025-03-02` → Returns transactions in the range of dates
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        paginator = self.pagination_class()
        if not request.user.has_earning_account:
            queryset = Transaction.objects.none()
        else:
            queryset = getattr(request.user.earning_account, 'transactions', Transaction.objects.none()).all()

        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        parsed_start_date = parse_date(start_date or '')
        parsed_end_date = parse_date(end_date or '')

        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise ValidationError('End date must be after start date.')

        if parsed_start_date:
            queryset = queryset.filter(created__gte=parsed_start_date)

        if parsed_end_date:
            plus_end_date = parsed_end_date + timedelta(days=1)
            queryset = queryset.filter(created__lte=plus_end_date)

        # Paginate the queryset
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = transactions.ListTransactionsSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)
