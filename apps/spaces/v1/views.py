from commons.exceptions.types.spaces import SpaceNotFound
from credits.providers.stripe.utils import process_payment_intent_response
from django.db import transaction
from reservations.models import Reservation
from reservations.signals import space_has_been_reserved
from reservations.v1 import serializers as reservation_serializers
from reservations.v1.serializers import ReservationSpaceSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from spaces.models import BaseSpace, PaidSpace
from spaces.signals import space_deleted
from spaces.v1 import serializers
from spaces.v1.serializers import SpaceSerializer


class CreateFreeSpaceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateFreeSpaceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Space created successfully'}, status=status.HTTP_201_CREATED)


class CreatePaidSpaceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = serializers.CreatePaidSpaceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Space created successfully'}, status=status.HTTP_201_CREATED)


class CreateSpaceFeedbackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid, *args, **kwargs):
        user = request.user
        serializer = serializers.CreateSpaceFeedbackSerializer(
            data=request.data, context={'space_id': uuid, 'user': user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Space feedback created successfully'}, status=status.HTTP_201_CREATED)


class RetrieveDeleteSpaceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid, *args, **kwargs):
        space: BaseSpace = BaseSpace.objects.available().filter(uuid=uuid).last()
        if not space:
            raise SpaceNotFound()

        return Response(
            SpaceSerializer(space, context={'request': request, 'user': request.user}).data, status=status.HTTP_200_OK
        )

    @transaction.atomic
    def delete(self, request, uuid, *args, **kwargs):
        user = request.user
        space = getattr(user, 'spaces', BaseSpace.objects.none()).available().filter(uuid=uuid).last()
        if not space:
            raise SpaceNotFound()

        if isinstance(space.get_real_instance(), PaidSpace):
            Reservation.objects.pending().filter(space=space).delete()

        space.delete()
        transaction.on_commit(lambda: space_deleted.send(sender=None, instance=space))
        return Response({'message': 'Space deleted successfully'}, status=status.HTTP_201_CREATED)


class ReserveSpaceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid, *args, **kwargs):
        serializer = reservation_serializers.ReserveSpaceSerializer(
            data=request.data, context={'space_id': uuid, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        payment_intent, reservation = serializer.save()
        response_data = process_payment_intent_response(payment_intent)
        if response_data['status'] == 'failed':
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)
        if response_data['status'] == 'requires_action':
            return Response(data=response_data, status=status.HTTP_402_PAYMENT_REQUIRED)

        reservation.status = Reservation.Status.RESERVED
        reservation.save()
        space_has_been_reserved.send(sender=None, instance=reservation)
        serialized_data = ReservationSpaceSerializer(reservation, context={'user': request.user}).data
        return Response(data=serialized_data, status=status.HTTP_200_OK)


class ExtendSpaceExpirationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, uuid, *args, **kwargs):
        serializer = serializers.ExtendSpaceExpirationSerializer(
            data=request.data, context={'space_id': uuid, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        space = serializer.extend_expiration()

        return Response(
            SpaceSerializer(space, context={'request': request, 'user': request.user}).data, status=status.HTTP_200_OK
        )


class ConfirmReservationSpaceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid, *args, **kwargs):
        serializer = reservation_serializers.ConfirmReservationSpaceSerializer(
            data=request.data, context={'space_id': uuid, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Space reservation has been confirmed'}, status=status.HTTP_201_CREATED)
