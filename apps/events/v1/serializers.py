from datetime import timedelta

from commons.exceptions.base import InvalidCoordinates
from commons.exceptions.types import events as events_exceptions
from commons.serializers import LocationInputSerializer
from commons.utils import global_preferences
from commons.validators import is_valid_coordinates
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from events.models import Event, EventFeedback
from events.settings import EXPIRATION_TIME_FOR_EVENTS_DYNAMIC_PREFERENCE
from events.signals import event_created, event_feedback_created


class CreateEventSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Event.Type.choices)
    location = LocationInputSerializer(source='*')

    def validate(self, attrs):
        if not is_valid_coordinates(attrs['lat'], attrs['lng']):
            raise InvalidCoordinates()
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
            expiration_time_in_hours = global_preferences[EXPIRATION_TIME_FOR_EVENTS_DYNAMIC_PREFERENCE]
            expires_at = timezone.now() + timedelta(hours=expiration_time_in_hours)
            event = Event.objects.create(
                owner=request.user,
                type=validated_data['type'],
                street_name=validated_data['street_name'],
                latitude=validated_data['lat'],
                longitude=validated_data['lng'],
                expires_at=expires_at,
            )
            # Call signal only AFTER the transaction commits
            transaction.on_commit(lambda: event_created.send(sender=None, instance=event))
            return event
        except Exception:
            raise events_exceptions.EventPublicationError()


class EventSerializer(serializers.Serializer):
    """Serializer for events"""

    id = serializers.UUIDField(source='uuid', format='hex')
    type = serializers.CharField()
    geohash = serializers.CharField()
    location = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    created = serializers.DateTimeField()

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


class CreateEventFeedbackSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=EventFeedback.Type.choices)

    def _get_event(self):
        event_id = self.context['event_id']
        event = Event.objects.available().filter(uuid=event_id).last()
        if not event:
            raise events_exceptions.EventNotFound()

        return event

    def validate(self, attrs):
        event = self._get_event()
        user = self.context['user']

        if event.owner == user:
            raise events_exceptions.EventOwnerCanNotSendFeedback()

        event_feedback = EventFeedback.objects.filter(type=attrs['type'], event=event, reported_by=user).last()
        if event_feedback:
            raise events_exceptions.EventFeedbackAlreadyCreated()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        event = self._get_event()
        user = self.context['user']
        event_feedback = EventFeedback.objects.create(type=validated_data['type'], event=event, reported_by=user)
        event_feedback_created.send(sender=None, instance=event_feedback)
        return event_feedback
