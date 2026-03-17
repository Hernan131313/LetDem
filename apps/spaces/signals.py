from datetime import timedelta

import waffle
from commons.utils import generate_coordinates_geohash, global_preferences, send_refresh_users_event
from django.dispatch import Signal, receiver
from django.utils import timezone

from spaces.models import BaseSpace, PaidSpace, SpaceFeedback
from spaces.settings import MINUTES_BEFORE_SPACE_EXPIRATION, POINTS_PER_SPACE_OCCUPIED_DYNAMIC_PREFERENCE
from spaces.tasks import (
    compress_image_task,
    remind_space_about_to_expire_notification_task,
    send_notification_for_scheduled_places,
    send_notification_for_space_occupied,
    space_has_been_expired,
)

space_created = Signal()
space_deleted = Signal()
space_feedback_created = Signal()
space_expiration_extended = Signal()


@receiver(space_created)
def space_created_handler(sender, instance: BaseSpace, **kwargs):
    from maps.signals import refresh_maps

    # Compress image
    if waffle.switch_is_active('enable_space_image_compression'):
        compress_image_task.delay(instance.pk)

    # ✅ FIX: usar latitud y longitud correctas
    instance.geohash = generate_coordinates_geohash(instance.latitude, instance.longitude)
    instance.save()

    refresh_maps.send(None, instance=instance)
    space_has_been_expired.apply_async(args=[instance.id], eta=instance.expires_at)

    send_notification_for_scheduled_places.delay(instance.uuid.hex)

    if isinstance(instance.get_real_instance(), PaidSpace):
        # Set last parked place new value
        instance.owner.car.update_last_parked_place(instance)

        minutes_before_to_notify = global_preferences[MINUTES_BEFORE_SPACE_EXPIRATION]
        future_time = timezone.now() + timedelta(minutes=minutes_before_to_notify)
        if instance.expires_at < future_time:
            return

        send_refresh_users_event(users=[instance.owner])
        remind_space_about_to_expire_notification_task.apply_async(
            args=[instance.id], eta=instance.expires_at - timedelta(minutes=minutes_before_to_notify)
        )


@receiver(space_feedback_created)
def space_feedback_created_handler(sender, instance: SpaceFeedback, **kwargs):
    from accounts.models import Contribution, User
    from maps.signals import refresh_maps

    if instance.type != SpaceFeedback.Type.TAKE_IT:
        space = instance.space
        space.decrease()
        space.refresh_from_db()
        if not space.is_expired:
            return

        refresh_maps.send(None, instance=instance.space)

    instance.space.expire()
    refresh_maps.send(None, instance=instance.space)
    if not instance.space.owner:
        return

    if car := getattr(instance.reported_by, 'car', None):
        car.update_last_parked_place(instance.space)

    points_per_space_occupied = global_preferences[POINTS_PER_SPACE_OCCUPIED_DYNAMIC_PREFERENCE]
    Contribution.objects.create(
        user=instance.space.owner,
        type=Contribution.Type.SPACE,
        action=Contribution.Action.SPACE_OCCUPIED,
        points=points_per_space_occupied,
    )
    user = User.objects.filter(id=instance.space.owner.id).select_for_update().last()
    user.total_points += points_per_space_occupied
    user.save(update_fields=['total_points', 'modified'])

    send_notification_for_space_occupied.delay(instance.space.uuid.hex, points=points_per_space_occupied)


@receiver(space_deleted)
def space_deleted_handler(sender, instance: BaseSpace, **kwargs):
    from maps.signals import refresh_maps

    send_refresh_users_event(users=[instance.owner])
    refresh_maps.send(None, instance=instance)


@receiver(space_expiration_extended)
def space_expiration_extended_handler(sender, instance: BaseSpace, **kwargs):
    from maps.signals import refresh_maps

    send_refresh_users_event(users=[instance.owner])
    refresh_maps.send(None, instance=instance)
