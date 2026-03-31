from alerts.models import Alert
from alerts.v1.serializers import AlertSerializer
from events.models import Event
from events.v1.serializers import EventSerializer
from spaces.models import BaseSpace
from spaces.v1.serializers import SpaceSerializer


def serializer_events(request, current_point: list, radius: int, **kwargs):
    user = kwargs.get('user')

    events_qs = Event.objects.nearby(float(current_point[0]), float(current_point[1]), radius)
    if user and not user.user_preferences.police_alert:
        events_qs = events_qs.exclude(type=Event.Type.POLICE)
    if user and not user.user_preferences.accident_alert:
        events_qs = events_qs.exclude(type=Event.Type.ACCIDENT)
    if user and not user.user_preferences.road_closed_alert:
        events_qs = events_qs.exclude(type=Event.Type.CLOSED_ROAD)

    return EventSerializer(events_qs, many=True, context={'user': user}).data


def serializer_spaces(request, current_point: list, radius: int, **kwargs):
    user = kwargs.get('user')
    if user and not user.user_preferences.available_spaces:
        return []

    spaces_qs = BaseSpace.objects.nearby(float(current_point[0]), float(current_point[1]), radius)
    return SpaceSerializer(spaces_qs, many=True, context={'user': request.user}).data


def serializer_alerts(request, current_point: list, radius: int, **kwargs):
    previous_point = kwargs.get('previous_point')
    user = kwargs.get('user')
    if not previous_point:
        return []

    alerts_qs = Alert.objects.in_front(current_point, previous_point, radius, user=user)
    if user and not user.user_preferences.radar_alert:
        alerts_qs = [alert for alert in alerts_qs if alert.type != Alert.Type.RADAR]
    if user and not user.user_preferences.camera_alert:
        alerts_qs = [alert for alert in alerts_qs if alert.type != Alert.Type.CAMERA]

    return AlertSerializer(alerts_qs, many=True, context={'request': request}).data
