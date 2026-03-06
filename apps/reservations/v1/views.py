from commons.exceptions.types.reservations import CancelReservationError, ReservationNotFound
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reservations.models import Reservation
from reservations.signals import reservation_cancelled
from reservations.v1 import serializers as reservation_serializers


class ConfirmReservationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid, *args, **kwargs):
        data = {'reservation_id': str(uuid), **request.data}
        serializer = reservation_serializers.ConfirmReservationSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Reservation has been confirmed'}, status=status.HTTP_201_CREATED)


class CancelReservationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, uuid, *args, **kwargs):
        user = request.user
        reservation: Reservation = (
            Reservation.objects.pending_to_confirm()
            .filter(
                Q(space__owner=user) | Q(reserved_by=user),
                uuid=uuid,
            )
            .first()
        )

        if not reservation:
            raise ReservationNotFound()

        try:
            reservation.status = Reservation.Status.CANCELLED
            reservation.cancelled_by = user
            reservation.save()
            reservation.cancel()
        except Exception:
            raise CancelReservationError()

        reservation_cancelled.send(None, instance=reservation)
        return Response(data={'message': 'Reservation has been cancelled'}, status=status.HTTP_200_OK)
