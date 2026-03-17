import logging

from celery import shared_task
from commons.push_notifications.onesignal.handlers import send_push_notification
from commons.push_notifications.onesignal.settings import (
    REMIND_CONFIRM_RESERVATION_NOTIFICATION,
    RESERVATION_CANCELLED_OWNER,
    RESERVATION_CANCELLED_REQUESTER,
)
from commons.utils import global_preferences, send_refresh_users_event
from django.db import transaction

from reservations.models import Reservation
from reservations.settings import MINUTES_BEFORE_CANCEL_RESERVATION

logger = logging.getLogger(__name__)


@shared_task
def reminder_to_confirm_reservation_task(reservation_id: int):
    reservation = Reservation.objects.pending_to_confirm().filter(id=reservation_id).last()
    if not reservation:
        return

    user = reservation.space.owner
    notification_data = {'page_to_redirect': 'reservation_details'}
    minutes_before_to_notify = global_preferences[MINUTES_BEFORE_CANCEL_RESERVATION]

    if user.user_preferences.push:
        for user_device in user.user_devices.all():
            device_id = user_device.device_id
            send_push_notification(
                device_id,
                notification_type=REMIND_CONFIRM_RESERVATION_NOTIFICATION,
                notification_data=notification_data,
                params={'minutes': minutes_before_to_notify},
            )


@shared_task
def cancel_not_confirmed_reservation_task(reservation_id: int):
    reservation = Reservation.objects.to_be_cancelled().filter(id=reservation_id).last()
    if not reservation or not reservation.reserved_by:
        return

    try:
        with transaction.atomic():
            reservation.status = Reservation.Status.CANCELLED
            reservation.metadata = reservation.metadata or {}
            reservation.metadata['cancellation_reason'] = 'not confirmed'
            reservation.save()
            reservation.cancel()
    except Exception:
        logger.info(f'Error cancelling reservation [uuid]: {reservation.uuid.hex}')
        return

    send_refresh_users_event(users=[reservation.space.owner, reservation.reserved_by])

    try:
        user_requester = reservation.reserved_by
        notification_data = {'page_to_redirect': 'activities'}
        if user_requester.user_preferences.push:
            for user_device in user_requester.user_devices.all():
                device_id = user_device.device_id
                send_push_notification(
                    device_id,
                    notification_type=RESERVATION_CANCELLED_REQUESTER,
                    notification_data=notification_data,
                    params={},
                )
    except Exception as e:
        logger.info(f'Exception error [requester]: {e}')

    try:
        user_owner = reservation.space.owner
        if user_owner.user_preferences.push:
            notification_data = {'page_to_redirect': 'activities'}
            for user_device in user_owner.user_devices.all():
                device_id = user_device.device_id
                send_push_notification(
                    device_id,
                    notification_type=RESERVATION_CANCELLED_OWNER,
                    notification_data=notification_data,
                    params={},
                )
    except Exception as e:
        logger.info(f'Exception error [owner]: {e}')
