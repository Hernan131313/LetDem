from datetime import timedelta

from commons.exceptions.base import InvalidCoordinates, InvalidPhoneNumber
from commons.exceptions.types import accounts as accounts_exceptions
from commons.exceptions.types import credits as credits_exceptions
from commons.exceptions.types import reservations as reservations_exceptions
from commons.exceptions.types import spaces as spaces_exceptions
from commons.serializers import LocationInputSerializer
from commons.utils import global_preferences
from commons.validators import is_valid_coordinates, is_valid_phone_number
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_extra_fields.fields import Base64ImageField
from reservations.models import Reservation
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from spaces.models import BaseSpace, FreeSpace, PaidSpace, SpaceFeedback
from spaces.settings import (
    EXPIRATION_TIME_FOR_SPACES_DYNAMIC_PREFERENCE,
    MAXIMUM_SPACE_PRICE,
    MAXIMUM_SPACE_TIME_TO_WAIT,
    MINIMUM_DISTANCE_TO_PUBLISH_SPACE_DYNAMIC_PREFERENCE,
    MINIMUM_SPACE_PRICE,
    MINIMUM_SPACE_TIME_TO_WAIT,
    MINIMUM_TIME_TO_PUBLISH_SPACE_DYNAMIC_PREFERENCE,
)
from spaces.signals import space_created, space_expiration_extended, space_feedback_created


class CreateSpaceSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=FreeSpace.Type.choices)
    image = Base64ImageField()
    location = LocationInputSerializer(source='*')

    class Meta:
        fields = ['type', 'location', 'image']

    def validate(self, data):
        """
        Validates:
        - location: check if provided coordinates are valid
        - distance: the minimum distance one user can publish spaces in a minimum period of time.
        """

        request = self.context['request']
        user = request.user

        latitude, longitude = float(data['lat']), float(data['lng'])
        if not is_valid_coordinates(latitude, longitude):
            raise InvalidCoordinates()

        if not hasattr(user, 'spaces'):
            return data

        distance_in_meters = global_preferences[MINIMUM_DISTANCE_TO_PUBLISH_SPACE_DYNAMIC_PREFERENCE]
        minutes_to_publish = global_preferences[MINIMUM_TIME_TO_PUBLISH_SPACE_DYNAMIC_PREFERENCE]
        less_than_15_minutes = timezone.now() - timedelta(minutes=minutes_to_publish)

        last_available_space = user.spaces.nearby(latitude, longitude, meters=distance_in_meters).first()
        if last_available_space and last_available_space.created > less_than_15_minutes:
            raise spaces_exceptions.SpacePublishedNearByRecently()

        return data


class CreateFreeSpaceSerializer(CreateSpaceSerializer):
    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
            expiration_time_in_hours = global_preferences[EXPIRATION_TIME_FOR_SPACES_DYNAMIC_PREFERENCE]
            expires_at = timezone.now() + timedelta(hours=expiration_time_in_hours)
            free_space = FreeSpace.objects.create(
                owner=request.user,
                type=validated_data['type'],
                image=validated_data['image'],
                street_name=validated_data['street_name'],
                latitude=validated_data['lat'],
                longitude=validated_data['lng'],
                expires_at=expires_at,
            )

            transaction.on_commit(lambda: space_created.send(sender=None, instance=free_space))
            return free_space
        except Exception as exc:
            raise serializers.ValidationError({'error': str(exc)}) from exc


class CreatePaidSpaceSerializer(CreateSpaceSerializer):
    price = serializers.DecimalField(max_digits=6, decimal_places=2)
    time_to_wait = serializers.IntegerField()
    phone = serializers.CharField()

    def validate(self, data):
        """
        Validates:
        - user car: check if the user has created a car
        - price: check if the price is valid
        - time_to_wait: check the maximum and minimum the user should wait for reservation
        - phone: check if user number is valid
        """

        data = super().validate(data)
        user = self.context['request'].user
        if not user.has_accepted_account:
            raise credits_exceptions.EarningAccountIsNotAccepted()

        if not getattr(user, 'car', None):
            raise accounts_exceptions.UserDoesNotHaveCar()

        user_has_active_reservation = Reservation.objects.active().pending().filter(space__owner=user).exists()
        if user_has_active_reservation:
            raise reservations_exceptions.ActiveReservationAlreadyExist()

        user_has_pending_to_confirm_reservation = (
            Reservation.objects.pending_to_confirm().filter(Q(reserved_by=user) | Q(space__owner=user)).exists()
        )
        if user_has_pending_to_confirm_reservation:
            raise reservations_exceptions.ActiveReservationAlreadyExist()

        minimum_price = global_preferences[MINIMUM_SPACE_PRICE]
        maximum_price = global_preferences[MAXIMUM_SPACE_PRICE]
        if data['price'] < minimum_price or data['price'] > maximum_price:
            raise spaces_exceptions.SpaceInvalidPrice(
                detail=f'Space price should be in range of {minimum_price} - {maximum_price}'
            )

        minimum_time_to_wait = global_preferences[MINIMUM_SPACE_TIME_TO_WAIT]
        maximum_time_to_wait = global_preferences[MAXIMUM_SPACE_TIME_TO_WAIT]
        if data['time_to_wait'] < minimum_time_to_wait or data['time_to_wait'] > maximum_time_to_wait:
            raise spaces_exceptions.SpaceInvalidTimeToWait(
                detail=f'Space time_to_wait should be in '
                f'range of {minimum_time_to_wait} - {maximum_time_to_wait} minutes'
            )

        if not is_valid_phone_number(data['phone']):
            raise InvalidPhoneNumber()

        return data

    @transaction.atomic
    def create(self, validated_data):
        from reservations.models import Reservation

        try:
            request = self.context['request']
            expires_at = timezone.now() + timedelta(minutes=validated_data['time_to_wait'])
            paid_space = PaidSpace.objects.create(
                owner=request.user,
                type=validated_data['type'],
                image=validated_data['image'],
                street_name=validated_data['street_name'],
                latitude=validated_data['lat'],
                longitude=validated_data['lng'],
                price=validated_data['price'] * 100,
                phone=validated_data['phone'],
                expires_at=expires_at,
            )

            Reservation.objects.create(
                space=paid_space,
                status=Reservation.Status.PENDING,
            )
            transaction.on_commit(lambda: space_created.send(sender=None, instance=paid_space))
            return paid_space
        except Exception as exc:
            raise serializers.ValidationError({'error': str(exc)}) from exc


class BaseSpaceSerializer(serializers.ModelSerializer):
    """Base serializer for all space types"""

    id = serializers.UUIDField(source='uuid', format='hex')
    image = serializers.ImageField(use_url=True)
    location = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    def get_is_owner(self, instance):
        user = self.context['user']
        return user == instance.owner

    def get_location(self, instance):
        return {
            'street_name': instance.street_name,
            'point': {
                'lng': float(instance.longitude),
                'lat': float(instance.latitude),
            },
        }

    class Meta:
        model = BaseSpace
        fields = ['id', 'type', 'image', 'is_owner', 'location', 'expires_at', 'created']


class FreeSpaceSerializer(BaseSpaceSerializer):
    """Serializer for FreeSpace"""

    class Meta:
        model = FreeSpace
        fields = BaseSpaceSerializer.Meta.fields


class PaidSpaceSerializer(BaseSpaceSerializer):
    """Serializer for FreeSpace"""

    price = serializers.DecimalField(max_digits=6, decimal_places=2, source='format_price')

    class Meta:
        model = PaidSpace
        fields = BaseSpaceSerializer.Meta.fields + ['price', 'phone']


class SpaceSerializer(PolymorphicSerializer):
    """Polymorphic Serializer to handle all BaseSpace subclasses"""

    model_serializer_mapping = {
        FreeSpace: FreeSpaceSerializer,
        PaidSpace: PaidSpaceSerializer,
    }


class CreateSpaceFeedbackSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=SpaceFeedback.Type.choices)

    def _get_space(self):
        space_id = self.context['space_id']
        space = BaseSpace.objects.available().filter(uuid=space_id).last()
        if not space:
            raise spaces_exceptions.SpaceNotFound()

        return space

    def validate(self, attrs):
        space = self._get_space()
        user = self.context['user']

        if space.owner == user:
            raise spaces_exceptions.SpaceOwnerCanNotSendFeedback()

        space_feedback = SpaceFeedback.objects.filter(type=attrs['type'], space=space, reported_by=user).last()
        if space_feedback:
            raise spaces_exceptions.SpaceFeedbackAlreadyCreated()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        space = self._get_space()
        user = self.context['user']
        space_feedback = SpaceFeedback.objects.create(type=validated_data['type'], space=space, reported_by=user)
        space_feedback_created.send(sender=None, instance=space_feedback)
        return space_feedback


class ExtendSpaceExpirationSerializer(serializers.Serializer):
    time_to_wait = serializers.IntegerField()

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.context['request'].user
        space_id = self.context['space_id']
        paid_space = BaseSpace.objects.available().filter(uuid=space_id, owner=user).last()
        if not paid_space or not isinstance(paid_space, PaidSpace):
            raise spaces_exceptions.SpaceNotFound()

        minimum_time_to_wait = global_preferences[MINIMUM_SPACE_TIME_TO_WAIT]
        maximum_time_to_wait = global_preferences[MAXIMUM_SPACE_TIME_TO_WAIT]
        if data['time_to_wait'] < minimum_time_to_wait or data['time_to_wait'] > maximum_time_to_wait:
            raise spaces_exceptions.SpaceInvalidTimeToWait(
                detail=f'Space time_to_wait should be in '
                f'range of {minimum_time_to_wait} - {maximum_time_to_wait} minutes'
            )

        return {'space': paid_space, **data}

    @transaction.atomic
    def extend_expiration(self):
        _validated_data = self.validated_data
        space = _validated_data.get('space')
        time_to_wait = _validated_data.get('time_to_wait')

        space.expires_at = space.expires_at + timedelta(minutes=time_to_wait)
        space.save()
        transaction.on_commit(lambda: space_expiration_extended.send(sender=None, instance=space))
        return space
