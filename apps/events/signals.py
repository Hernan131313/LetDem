from commons.utils import generate_coordinates_geohash, global_preferences
from django.dispatch import Signal, receiver

from events.models import Event, EventFeedback
from events.settings import POINTS_PER_EVENT_CREATION_DYNAMIC_PREFERENCE
from events.tasks import event_has_been_expired, send_event_confirmed_notification_task

event_created = Signal()
event_feedback_created = Signal()


@receiver(event_created)
def event_created_handler(sender, instance: Event, **kwargs):
    from maps.signals import refresh_maps

    instance.geohash = generate_coordinates_geohash(instance.latitude, instance.latitude)
    instance.save()

    refresh_maps.send(None, instance=instance)
    event_has_been_expired.apply_async(args=[instance.id], eta=instance.expires_at)


@receiver(event_feedback_created)
def event_feedback_created_handler(sender, instance: EventFeedback, **kwargs):
    from accounts.models import Contribution, User
    from maps.signals import refresh_maps

    if instance.type != EventFeedback.Type.IS_THERE:
        event = instance.event
        event.decrease_time()
        event.refresh_from_db()
        if not event.is_expired:
            return

        refresh_maps.send(None, instance=event)

    instance.event.increase_time()
    if instance.event.contribution_received:
        return

    points_per_event_creation = global_preferences[POINTS_PER_EVENT_CREATION_DYNAMIC_PREFERENCE]
    Contribution.objects.create(
        user=instance.event.owner,
        type=Contribution.Type.EVENT,
        action=Contribution.Action.EVENT_CREATED,
        points=points_per_event_creation,
    )
    instance.event.metadata = instance.event.metadata or {}
    instance.event.metadata['contribution_created'] = True
    instance.event.save()

    user = User.objects.filter(id=instance.event.owner.id).select_for_update().last()
    user.total_points += points_per_event_creation
    user.save(update_fields=['total_points', 'modified'])

    send_event_confirmed_notification_task.delay(instance.uuid.hex, points=points_per_event_creation)
