from commons.exceptions.base import InvalidCoordinates
from commons.exceptions.types import accounts as accounts_exceptions
from commons.serializers import LocationInputSerializer
from commons.settings import METERS_TO_SHOW_TOO_CLOSE_MODAL
from commons.utils import global_preferences
from commons.validators import is_valid_coordinates
from credits.settings import MINIMUM_AMOUNT_TO_WITHDRAW
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from spaces.settings import (
    MAXIMUM_SPACE_PRICE,
    MAXIMUM_SPACE_TIME_TO_WAIT,
    MINIMUM_SPACE_PRICE,
    MINIMUM_SPACE_TIME_TO_WAIT,
)

from accounts import models as accounts_models
from accounts.models import UserDevice


class ContributionSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    type = serializers.CharField()
    action = serializers.CharField()
    points = serializers.IntegerField()
    created = serializers.DateTimeField()

    class Meta:
        fields = ['id', 'type', 'action', 'points', 'created']


class UpdateUserInfoSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = accounts_models.User
        fields = ['first_name', 'last_name']

    def update(self, instance, validated_data):
        # Update the instance with the validated data
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance


class AlertsPreferencesSerializer(serializers.Serializer):
    available_spaces = serializers.BooleanField(required=False)
    radar_alert = serializers.BooleanField(required=False)
    camera_alert = serializers.BooleanField(required=False)
    prohibited_zone_alert = serializers.BooleanField(required=False)
    speed_limit_alert = serializers.BooleanField(required=False)
    fatigue_alert = serializers.BooleanField(required=False)
    police_alert = serializers.BooleanField(required=False)
    accident_alert = serializers.BooleanField(required=False)
    road_closed_alert = serializers.BooleanField(required=False)


class NotificationSettingsSerializer(serializers.Serializer):
    email = serializers.BooleanField(required=False)
    push = serializers.BooleanField(required=False)

    class Meta:
        fields = ['email', 'push']


class UpdateUserPreferences(serializers.Serializer):
    alerts = AlertsPreferencesSerializer(required=False)
    notifications = NotificationSettingsSerializer(required=False)

    def update(self, user: accounts_models.User, validated_data):
        user_preferences, _ = accounts_models.UserPreferences.objects.get_or_create(user=user)

        alerts = validated_data.get('alerts', {})
        for field, value in alerts.items():
            setattr(user_preferences, field, value)

        notifications = validated_data.get('notifications', {})
        for field, value in notifications.items():
            setattr(user_preferences, field, value)

        user_preferences.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=False)
    new_password = serializers.CharField(required=False)

    def validate(self, attrs):
        user: accounts_models.User = self.instance

        if attrs['current_password'] == attrs['new_password']:
            raise accounts_exceptions.RepeatedPassword()

        if not user.check_password(attrs['current_password']):
            raise accounts_exceptions.InvalidCurrentPassword()

        return attrs

    def update(self, instance: accounts_models.User, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', source='uuid')
    contributions = serializers.SerializerMethodField()
    notifications_count = serializers.SerializerMethodField()
    alerts_preferences = serializers.SerializerMethodField()
    notifications_preferences = serializers.SerializerMethodField()
    earning_account = serializers.SerializerMethodField()
    active_reservation = serializers.SerializerMethodField()
    default_payment_method = serializers.SerializerMethodField()
    constants_settings = serializers.SerializerMethodField()
    device_id = serializers.SerializerMethodField()

    class Meta:
        model = accounts_models.User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'is_social',
            'language',
            'active_reservation',
            'contributions',
            'total_points',
            'notifications_count',
            'alerts_preferences',
            'default_payment_method',
            'notifications_preferences',
            'earning_account',
            'constants_settings',
            'device_id',
        ]

    def get_contributions(self, instance):
        if not hasattr(instance, 'contributions'):
            return []
        queryset = instance.contributions.recents()
        return ContributionSerializer(queryset, many=True).data

    def get_notifications_count(self, instance):
        if not hasattr(instance, 'notifications'):
            return 0
        return instance.notifications.unread().count()

    def get_alerts_preferences(self, instance):
        if not hasattr(instance, 'user_preferences'):
            return None

        return AlertsPreferencesSerializer(instance.user_preferences).data

    def get_notifications_preferences(self, instance):
        if not hasattr(instance, 'user_preferences'):
            return None

        return NotificationSettingsSerializer(instance.user_preferences).data

    def get_default_payment_method(self, instance):
        from credits.v1.serializers.payment_methods import PaymentMethodSerializer

        if not hasattr(instance, 'payment_methods'):
            return None
        pm = instance.payment_methods.filter(is_default=True).last()
        if not pm:
            return

        return PaymentMethodSerializer(pm).data

    def get_earning_account(self, instance):
        from credits.v1.serializers.earnings import RetrieveEarningAccountSerializer

        if not hasattr(instance, 'earning_account'):
            return None
        return RetrieveEarningAccountSerializer(instance.earning_account).data

    def get_active_reservation(self, instance):
        from reservations.models import Reservation
        from reservations.v1.serializers import ReservationSpaceSerializer

        reservation = (
            Reservation.objects.active().pending().filter(space__owner=instance).first()
            or Reservation.objects.pending_to_confirm()
            .filter(Q(reserved_by=instance) | Q(space__owner=instance))
            .first()
        )
        if not reservation:
            return None

        return ReservationSpaceSerializer(reservation, context={'user': instance}).data

    def get_constants_settings(self, _):
        return {
            'withdrawal_amount': {'minimum': global_preferences[MINIMUM_AMOUNT_TO_WITHDRAW], 'maximum': 1000},
            'space_price': {
                'minimum': global_preferences[MINIMUM_SPACE_PRICE],
                'maximum': global_preferences[MAXIMUM_SPACE_PRICE],
            },
            'space_time_to_wait': {
                'minimum': global_preferences[MINIMUM_SPACE_TIME_TO_WAIT],
                'maximum': global_preferences[MAXIMUM_SPACE_TIME_TO_WAIT],
            },
            'meters_to_show_too_close_modal': global_preferences[METERS_TO_SHOW_TOO_CLOSE_MODAL],
        }

    def get_device_id(self, obj):
        if device := obj.user_devices.first():
            return device.device_id
        return None


class CarSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', source='uuid')
    parked_place = serializers.SerializerMethodField()

    class Meta:
        model = accounts_models.Car
        fields = ['id', 'name', 'plate_number', 'label', 'parked_place']

    def get_parked_place(self, instance):
        parked_place = getattr(instance, 'parked_place', None)
        if not parked_place:
            return None

        return {
            'street_name': parked_place.street_name,
            'point': {
                'lng': float(parked_place.longitude),
                'lat': float(parked_place.latitude),
            },
        }


class CreateCarSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', source='uuid', read_only=True)
    parked_place = serializers.SerializerMethodField()

    class Meta:
        model = accounts_models.Car
        fields = ['id', 'name', 'plate_number', 'label', 'parked_place']

    def get_parked_place(self, instance):
        parked_place = getattr(instance, 'parked_place', None)
        if not parked_place:
            return None

        return {
            'street_name': parked_place.street_name,
            'point': {
                'lng': float(parked_place.longitude),
                'lat': float(parked_place.latitude),
            },
        }

    def validate(self, attrs):
        super().validate(attrs)

        user = self.context.get('user')
        if hasattr(user, 'car') and user.car is not None:
            raise accounts_exceptions.CarAlreadyCreated()
        attrs['user'] = user
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        return accounts_models.Car.objects.create(
            user=validated_data['user'],
            name=validated_data.get('name'),
            plate_number=validated_data.get('plate_number'),
            label=validated_data.get('label'),
        )


class UpdateCarSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', source='uuid', read_only=True)
    name = serializers.CharField(required=False)
    plate_number = serializers.CharField(required=False)
    label = serializers.CharField(required=False)
    parked_place = serializers.SerializerMethodField()

    class Meta:
        model = accounts_models.Car
        fields = ['id', 'name', 'plate_number', 'label', 'parked_place']

    def get_parked_place(self, instance):
        parked_place = getattr(instance, 'parked_place', None)
        if not parked_place:
            return None

        return {
            'street_name': parked_place.street_name,
            'point': {
                'lng': float(parked_place.longitude),
                'lat': float(parked_place.latitude),
            },
        }

    def validate_year(self, value):
        if value and value > timezone.now().year:
            raise serializers.ValidationError('This value cannot be greater than current year')
        return value

    def validate(self, attrs):
        super().validate(attrs)
        user = self.context.get('user')
        if not hasattr(user, 'car') or user.car is None:
            raise accounts_exceptions.UserDoesNotHaveCar()
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.plate_number = validated_data.get('plate_number', instance.plate_number)
        instance.label = validated_data.get('label', instance.label)
        instance.save()

        return instance


class CarParkedPlaceAddressSerializer(serializers.Serializer):
    parked_place = LocationInputSerializer(source='*')

    def to_representation(self, instance):
        return CarSerializer(instance).data

    def validate(self, attrs):
        user = self.context.get('user')
        if not hasattr(user, 'car') or user.car is None:
            raise accounts_exceptions.UserDoesNotHaveCar()

        if not is_valid_coordinates(attrs['lat'], attrs['lng']):
            raise InvalidCoordinates()

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        getattr(instance, 'parked_place', accounts_models.CarParkedPlace.objects.none()).delete()

        accounts_models.CarParkedPlace.objects.create(
            car=instance,
            street_name=validated_data['street_name'],
            latitude=validated_data['lat'],
            longitude=validated_data['lng'],
        )

        return instance


class FavoriteAddressSerializer(serializers.Serializer):
    id = serializers.UUIDField(format='hex', source='uuid')
    type = serializers.CharField()
    location = serializers.SerializerMethodField()

    def get_location(self, instance):
        return {
            'street_name': instance.street_name,
            'point': {
                'lng': float(instance.longitude),
                'lat': float(instance.latitude),
            },
        }


class BaseAddAddressSerializer(serializers.Serializer):
    address_type = NotImplemented
    address = LocationInputSerializer(source='*')

    def to_representation(self, instance):
        return FavoriteAddressSerializer(instance).data

    def validate(self, attrs):
        if not is_valid_coordinates(attrs['lat'], attrs['lng']):
            raise InvalidCoordinates()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['user']

        if hasattr(user, 'addresses'):
            user.addresses.filter(type=self.address_type).delete()

        return accounts_models.FavoriteAddress.objects.create(
            user=user,
            type=self.address_type,
            street_name=validated_data['street_name'],
            latitude=validated_data['lat'],
            longitude=validated_data['lng'],
        )


class AddHomeAddressSerializer(BaseAddAddressSerializer):
    address_type = accounts_models.FavoriteAddress.Type.HOME


class AddWorkAddressSerializer(BaseAddAddressSerializer):
    address_type = accounts_models.FavoriteAddress.Type.WORK


class ScheduledNotificationSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    is_expired = serializers.BooleanField()
    radius = serializers.FloatField()
    location = serializers.SerializerMethodField()

    def get_location(self, instance):
        return {
            'street_name': instance.street_name,
            'point': {
                'lng': float(instance.longitude),
                'lat': float(instance.latitude),
            },
        }


class CreateScheduledNotificationSerializer(serializers.Serializer):
    location = LocationInputSerializer(source='*')
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    radius = serializers.FloatField()

    def validate(self, attrs):
        user = self.context['user']
        queryset = getattr(user, 'scheduled_notifications', accounts_models.ScheduledNotification.objects.none())

        if not is_valid_coordinates(attrs['lat'], attrs['lng']):
            raise InvalidCoordinates()

        # Check if the user has created a scheduled notification nearby (25 meters)
        if queryset.nearby(float(attrs['lat']), float(attrs['lng']), 25).exists():
            raise accounts_exceptions.NotificationAlreadyScheduledInPlace()

        time_now = timezone.now()
        if attrs['starts_at'] >= attrs['ends_at']:
            raise accounts_exceptions.EndsAndStartsTimeShouldBeGreater()

        if attrs['starts_at'] < time_now or attrs['ends_at'] < time_now:
            raise accounts_exceptions.EndsAndStartsTimeShouldBeGreaterThanNow()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['user']
        return accounts_models.ScheduledNotification.objects.create(
            user=user,
            starts_at=validated_data['starts_at'],
            ends_at=validated_data['ends_at'],
            radius=validated_data['radius'],
            street_name=validated_data['street_name'],
            latitude=validated_data['lat'],
            longitude=validated_data['lng'],
        )


class ReScheduledNotificationSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()

    def validate(self, attrs):
        time_now = timezone.now()
        if attrs['starts_at'] >= attrs['ends_at']:
            raise accounts_exceptions.EndsAndStartsTimeShouldBeGreater()

        if attrs['starts_at'] < time_now or attrs['ends_at'] < time_now:
            raise accounts_exceptions.EndsAndStartsTimeShouldBeGreaterThanNow()

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.starts_at = validated_data['starts_at']
        instance.ends_at = validated_data['ends_at']
        instance.save()
        return instance


class NotificationSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    type = serializers.CharField()
    read = serializers.BooleanField()
    notification_object = serializers.SerializerMethodField()
    created = serializers.DateTimeField()

    def get_notification_object(self, obj):
        """Dynamically serialize the content object based on its type."""
        from spaces.models import FreeSpace, PaidSpace
        from spaces.v1.serializers import PaidSpaceSerializer, SpaceSerializer

        if isinstance(obj.content_object, FreeSpace):
            return SpaceSerializer(obj.content_object, context={'user': obj.user}).data
        if isinstance(obj.content_object, PaidSpace):
            return PaidSpaceSerializer(obj.content_object, context={'user': obj.user}).data
        return None


class ChangeUserLanguageSerializer(serializers.Serializer):
    language_code = serializers.ChoiceField(
        choices=accounts_models.User.Languages.choices, allow_null=False, allow_blank=False
    )

    def update(self, instance: accounts_models.User, validated_data):
        instance.language = validated_data['language_code']
        instance.save()
        return instance


class UpdateDeviceIdSerializer(serializers.Serializer):
    device_id = serializers.CharField(allow_null=False, allow_blank=False)

    def update(self, instance: accounts_models.User, validated_data):
        device_id = validated_data['device_id']
        UserDevice.objects.filter(device_id=device_id).delete()
        UserDevice.objects.create(user=instance, device_id=device_id)
        return instance
