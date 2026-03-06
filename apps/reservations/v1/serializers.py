from datetime import timedelta

from commons.exceptions.types import reservations as reservations_exceptions
from commons.exceptions.types import spaces as spaces_exceptions
from commons.exceptions.types.credits import PaymentMethodNotFound
from commons.exceptions.types.reservations import (
    ConfirmReservationError,
    InvalidConfirmationCode,
    ReservationCancelledError,
    ReservationNotFound,
    SpaceAlreadyReserved,
    SpaceOwnerCannotReserve,
)
from commons.utils import global_preferences
from credits.models import PaymentMethod
from credits.providers.stripe.utils import create_payment_intent
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from spaces.models import BaseSpace, PaidSpace

from reservations.models import Reservation
from reservations.settings import MINUTES_TO_CANCEL_RESERVATION
from reservations.signals import reservation_confirmed


class ReservationSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=6, decimal_places=2, source='format_price')
    type = serializers.CharField(source='space.type')
    status = serializers.CharField()
    street = serializers.CharField(source='space.street_name')
    created = serializers.DateTimeField()


class ReservationSpaceSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    is_owner = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    cancelled_at = serializers.DateTimeField()

    # for requester
    confirmation_code = serializers.SerializerMethodField()
    car_plate_number = serializers.SerializerMethodField()

    def get_space(self, instance):
        from spaces.v1.serializers import PaidSpaceSerializer

        return PaidSpaceSerializer(instance.space, context=self.context).data

    def get_is_owner(self, instance):
        user = self.context['user']
        return instance.space.owner == user

    def get_car_plate_number(self, instance):
        return instance.space.owner.car.plate_number

    def get_confirmation_code(self, instance):
        return instance.confirmation_code

    def get_status(self, instance):
        return instance.status

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['user']
        if self.instance.space.owner == user:
            self.fields.pop('confirmation_code')
            self.fields.pop('car_plate_number')


class ReserveSpaceSerializer(serializers.Serializer):
    payment_method_id = serializers.UUIDField()

    def validate(self, attrs):
        user = self.context['request'].user
        space_id = self.context['space_id']
        paid_space = BaseSpace.objects.available().filter(uuid=space_id).last()
        if not paid_space or not isinstance(paid_space, PaidSpace):
            raise spaces_exceptions.SpaceNotFound()

        if paid_space.owner == user:
            raise SpaceOwnerCannotReserve()

        user_has_active_reservation = Reservation.objects.active().pending().filter(space__owner=user).exists()
        if user_has_active_reservation:
            raise reservations_exceptions.ActiveReservationAlreadyExist()

        active_reserved_space = (
            Reservation.objects.pending_to_confirm().filter(Q(reserved_by=user) | Q(space__owner=user)).first()
        )
        if active_reserved_space:
            raise reservations_exceptions.ActiveReservationAlreadyExist()

        payment_method: PaymentMethod = PaymentMethod.objects.filter(user=user, uuid=attrs['payment_method_id']).last()
        if not payment_method:
            raise PaymentMethodNotFound()

        reserved_space: Reservation = Reservation.objects.reserved().filter(space=paid_space).first()
        if reserved_space:
            raise SpaceAlreadyReserved()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        space_id = self.context['space_id']

        paid_space = BaseSpace.objects.available().filter(uuid=space_id).last()
        reservation = Reservation.objects.active().pending().filter(space=paid_space).select_for_update().first()
        if not reservation:
            raise spaces_exceptions.SpaceNotFound()

        if reservation.is_locked:
            raise SpaceAlreadyReserved()

        reservation.lock()
        reservation.reserved_by = user
        reservation.reserved_by_user_email = user.email

        minutes_to_cancel = global_preferences[MINUTES_TO_CANCEL_RESERVATION]
        cancel_datetime = timezone.now() + timedelta(minutes=minutes_to_cancel)
        reservation.cancelled_at = cancel_datetime

        payment_method = PaymentMethod.objects.filter(user=user, uuid=validated_data['payment_method_id']).last()
        payment_intent = create_payment_intent(reservation, payment_method)
        reservation.payment_provider_id = payment_intent.id
        reservation.save()
        return payment_intent, reservation


class ConfirmReservationSpaceSerializer(serializers.Serializer):
    """DEPRECATED"""

    confirmation_code = serializers.CharField()

    def validate(self, attrs):
        user = self.context['request'].user
        space_id = self.context['space_id']

        reservation: Reservation = Reservation.objects.filter(
            space__uuid=space_id, status=Reservation.Status.RESERVED, space__owner=user
        ).first()

        if not reservation:
            raise ReservationNotFound()

        if reservation.confirmation_code != attrs['confirmation_code']:
            raise InvalidConfirmationCode()

        attrs['reservation'] = reservation
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        reservation: Reservation = validated_data['reservation']
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save()
        reservation.space.expires_at = timezone.now()
        reservation.space.save()
        reservation.capture()
        return reservation


class ConfirmReservationSerializer(serializers.Serializer):
    confirmation_code = serializers.CharField()
    reservation_id = serializers.CharField()

    def validate(self, attrs):
        user = self.context['request'].user
        reservation: Reservation = (
            Reservation.objects.pending_to_confirm().filter(uuid=attrs['reservation_id'], space__owner=user).first()
        )

        if not reservation:
            raise ReservationNotFound()

        if reservation.cancelled_at < timezone.now():
            raise ReservationCancelledError()

        if reservation.confirmation_code != attrs['confirmation_code']:
            raise InvalidConfirmationCode()

        attrs['reservation'] = reservation
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            reservation: Reservation = validated_data['reservation']
            reservation.status = Reservation.Status.CONFIRMED
            reservation.save()
            reservation.space.expires_at = timezone.now()
            reservation.space.save()
            reservation.capture()
            reservation_confirmed.send(sender=None, instance=reservation)
        except Exception:
            raise ConfirmReservationError()

        return reservation
