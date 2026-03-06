from celery import shared_task
from commons.push_notifications.onesignal.handlers import send_push_notification
from commons.push_notifications.onesignal.settings import EVENT_CONFIRMED_NOTIFICATION

from events.models import Event, EventFeedback


@shared_task
def send_event_confirmed_notification_task(event_feedback_id: str, points: int):
    instance = EventFeedback.objects.get(uuid=event_feedback_id)

    user = instance.event.owner
    for user_device in user.user_devices.all():
        if not user.user_preferences.push:
            break

        device_id = user_device.device_id
        notification_data = {'page_to_redirect': 'contributions'}
        send_push_notification(
            device_id,
            notification_type=EVENT_CONFIRMED_NOTIFICATION,
            notification_data=notification_data,
            params={'points': points},
        )


@shared_task
def event_has_been_expired(event_id: int):
    from maps.signals import refresh_maps

    event = Event.objects.filter(id=event_id).last()
    if not event:
        return

    refresh_maps.send(None, instance=event)
