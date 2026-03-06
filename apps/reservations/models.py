from datetime import timedelta

from commons.models import AbstractUUIDModel
from commons.utils import generate_confirmation_code, global_preferences
from credits.providers.stripe.utils import cancel_payment_intent, capture_payment_intent
from django.db import models
from django.utils import timezone
from spaces.settings import MINUTES_TO_BLOCK_SPACES


class Reservation(AbstractUUIDModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RESERVED = 'RESERVED', 'Reserved'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    reserved_by = models.ForeignKey(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations'
    )
    cancelled_by = models.ForeignKey(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='cancellations'
    )
    reserved_by_user_email = models.CharField(blank=True, null=True)
    space = models.ForeignKey('spaces.PaidSpace', related_name='reservations', on_delete=models.PROTECT)
    status = models.CharField(choices=Status.choices, default=Status.PENDING)
    confirmation_code = models.CharField(max_length=6, default=generate_confirmation_code)
    payment_provider_id = models.CharField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Queryset(models.QuerySet):
        def reserved(self):
            return self.filter(status__in=[self.model.Status.RESERVED, self.model.Status.CONFIRMED])

        def pending(self):
            return self.filter(status=self.model.Status.PENDING)

        def active(self):
            return self.filter(space__expires_at__gt=timezone.now())

        def pending_to_confirm(self):
            return self.filter(status=self.model.Status.RESERVED, cancelled_at__gt=timezone.now())

        def to_be_cancelled(self):
            return self.filter(status=self.model.Status.RESERVED, cancelled_at__lte=timezone.now())

    objects = models.Manager.from_queryset(Queryset)()

    def __str__(self):
        return f'{self.price} - {self.status}'

    @property
    def is_blocked(self):
        minutes_to_block = global_preferences[MINUTES_TO_BLOCK_SPACES]
        minutes_ago = timezone.now() - timedelta(minutes=minutes_to_block)
        return self.created > minutes_ago

    @property
    def price(self):
        return self.space.price

    @property
    def format_price(self):
        return self.space.format_price

    @property
    def is_reserved(self):
        return self.status == self.Status.RESERVED

    def capture(self):
        capture_payment_intent(self.payment_provider_id)

    def cancel(self):
        cancel_payment_intent(self.payment_provider_id)

    def lock(self):
        metadata = self.metadata or {}
        minutes_to_block = global_preferences[MINUTES_TO_BLOCK_SPACES]
        metadata['block_expires_at'] = int((timezone.now() + timedelta(minutes=minutes_to_block)).timestamp())
        self.save()

    def unlock(self):
        metadata = self.metadata or {}
        metadata['block_expires_at'] = int(timezone.now().timestamp())
        self.save()

    @property
    def is_locked(self):
        metadata = self.metadata or {}
        if metadata.get('block_expires_at') is None:
            return False

        minutes_to_block = global_preferences[MINUTES_TO_BLOCK_SPACES]
        releases_at = int((timezone.now() - timedelta(minutes=minutes_to_block)).timestamp())
        if metadata['block_expires_at'] > releases_at:
            return True

        return False
