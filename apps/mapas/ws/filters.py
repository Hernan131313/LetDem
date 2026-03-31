from events.models import Event
from events.v1.serializers import EventSerializer
from spaces.models import BaseSpace
from spaces.v1.serializers import SpaceSerializer


def filter_events(user, geohash):
    user.refresh_from_db()
    events_qs = Event.objects.available().filter(geohash=geohash)
    if not user.user_preferences.police_alert:
        events_qs = events_qs.exclude(type=Event.Type.POLICE)
    if not user.user_preferences.accident_alert:
        events_qs = events_qs.exclude(type=Event.Type.ACCIDENT)
    if not user.user_preferences.road_closed_alert:
        events_qs = events_qs.exclude(type=Event.Type.CLOSED_ROAD)

    return EventSerializer(events_qs, many=True, context={'user': user}).data


def filter_spaces(user, geohash):
    user.refresh_from_db()
    spaces_qs = BaseSpace.objects.available().filter(geohash=geohash)
    if not user.user_preferences.available_spaces:
        spaces_qs = BaseSpace.objects.none()

    return SpaceSerializer(spaces_qs, many=True, context={'user': user}).data


def retrieve_map_data(user, geohash):
    return {'spaces': filter_spaces(user, geohash), 'events': filter_events(user, geohash)}
