from commons.paginators import CustomPagination
from reservations.models import Reservation
from reservations.v1.serializers import ReservationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class ListOrdersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        paginator = self.pagination_class()
        queryset = Reservation.objects.filter(space__owner=request.user)
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = ReservationSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)


class ListReservationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        queryset = getattr(request.user, 'reservations', Reservation.objects.none()).all()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        response_data = ReservationSerializer(paginated_queryset, many=True).data
        return paginator.get_paginated_response(response_data)
