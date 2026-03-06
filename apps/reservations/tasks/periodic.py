import logging

from celery import shared_task
from commons.utils import send_refresh_users_event
from django.utils import timezone

from reservations.models import Reservation
from reservations.tasks.tasks import cancel_not_confirmed_reservation_task

logger = logging.getLogger(__name__)


@shared_task
def mark_expired_pending_reservations_to_status_expired_task():
    """
    Task to mark as expired all expired pending reservations.

    Steps:
    - Filter for expired reservations
    - Mark reservations as expired
    """

    now = timezone.now()
    Reservation.objects.filter(status=Reservation.Status.PENDING, space__expires_at__lt=now).update(
        status=Reservation.Status.EXPIRED
    )


@shared_task
def cancel_not_confirmed_reservation_periodic_task():
    reservations = Reservation.objects.to_be_cancelled()
    if not reservations.exists():
        return

    for reservation in reservations:
        # Send reservation update to the user
        send_refresh_users_event(users=[reservation.space.owner, reservation.reserved_by])
        cancel_not_confirmed_reservation_task.delay(reservation.id)
