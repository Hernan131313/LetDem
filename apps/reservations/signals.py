from datetime import timedelta

from accounts.models import Contribution, User
from commons.push_notifications.onesignal.handlers import send_push_notification
from commons.push_notifications.onesignal.settings import (
    RESERVATION_CANCELLED_OWNER,
    RESERVATION_CANCELLED_REQUESTER,
    RESERVATION_CONFIRMED_NOTIFICATION,
)
from commons.utils import global_preferences, send_refresh_users_event
from django.db import transaction
from django.db.models import F
from django.dispatch import Signal, receiver
from django.utils import timezone
from spaces.settings import POINTS_PER_SPACE_OCCUPIED_DYNAMIC_PREFERENCE
from spaces.tasks import send_space_reserved_notification_task

from reservations.models import Reservation
from reservations.settings import MINUTES_BEFORE_CANCEL_RESERVATION
from reservations.tasks.tasks import cancel_not_confirmed_reservation_task, reminder_to_confirm_reservation_task

space_has_been_reserved = Signal()
reservation_confirmed = Signal()
reservation_cancelled = Signal()


@receiver(space_has_been_reserved)
def space_has_been_reserved_handler(sender, instance: Reservation, **kwargs):
    minutes_before_to_notify = global_preferences[MINUTES_BEFORE_CANCEL_RESERVATION]
    send_space_reserved_notification_task.delay(instance.space.uuid.hex)
    cancel_not_confirmed_reservation_task.apply_async(
        args=[instance.id], eta=instance.cancelled_at + timedelta(seconds=1)
    )

    # Send reservation update to the user
    send_refresh_users_event(users=[instance.space.owner, instance.reserved_by])

    time_limit_before_cancel = timezone.now() + timedelta(minutes=minutes_before_to_notify)
    if instance.cancelled_at < time_limit_before_cancel:
        return

    reminder_to_confirm_reservation_task.apply_async(
        args=[instance.id], eta=instance.cancelled_at - timedelta(minutes=minutes_before_to_notify)
    )


@receiver(reservation_confirmed)
@transaction.atomic
def reservation_confirmed_handler(sender, instance: Reservation, **kwargs):
    """
    Notify user and award points when a reservation is confirmed.
    """
    reservation = instance  # already passed
    if not reservation or not reservation.reserved_by:
        return

    # Lock user for update (prevent race conditions on total_points)
    user = User.objects.select_for_update().get(pk=reservation.reserved_by_id)

    # Update last parked place if car exists
    if car := getattr(user, 'car', None):
        car.update_last_parked_place(reservation.space)

    # Points
    points_per_event_creation = global_preferences[POINTS_PER_SPACE_OCCUPIED_DYNAMIC_PREFERENCE]
    Contribution.objects.create(
        user=user,
        type=Contribution.Type.SPACE,
        action=Contribution.Action.SPACE_OCCUPIED,
        points=points_per_event_creation,
    )

    # Atomic points increment
    User.objects.filter(pk=user.pk).update(
        total_points=F('total_points') + points_per_event_creation, modified=timezone.now()
    )

    # Send reservation update to the user
    send_refresh_users_event(users=[reservation.space.owner, reservation.reserved_by])

    # Send notifications after commit (only if push enabled)
    if user.user_preferences.push:

        def send_notifications():
            devices = list(user.user_devices.values_list('device_id', flat=True))
            for device_id in devices:
                send_push_notification(
                    device_id,
                    notification_type=RESERVATION_CONFIRMED_NOTIFICATION,
                    notification_data={'page_to_redirect': 'contributions'},
                    params={'points': points_per_event_creation},
                )

        transaction.on_commit(lambda: send_notifications())


@receiver(reservation_cancelled)
def space_has_been_canceled_handler(sender, instance: Reservation, **kwargs):
    instance.refresh_from_db()
    if not instance.reserved_by and instance.cancelled_by != instance.space.owner:
        return

    if instance.cancelled_by == instance.reserved_by:
        user = instance.space.owner
        notification_type = RESERVATION_CANCELLED_OWNER
    else:
        user = instance.reserved_by
        notification_type = RESERVATION_CANCELLED_REQUESTER

    # Send reservation update to the user
    send_refresh_users_event(users=[instance.space.owner, instance.reserved_by])

    # Send notifications after commit (only if push enabled)
    if user.user_preferences.push:

        def send_notifications():
            devices = list(user.user_devices.values_list('device_id', flat=True))
            for device_id in devices:
                send_push_notification(
                    device_id,
                    notification_type=notification_type,
                    notification_data={'page_to_redirect': 'activities'},
                    params={},
                )

        transaction.on_commit(lambda: send_notifications())
