import os
from datetime import timedelta

from commons.models import AbstractUUIDModel
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone
from polymorphic.models import PolymorphicManager, PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from reservations.models import Reservation


def unique_upload_path(instance, filename):
    """Generate a unique filename to prevent overwriting"""
    ext = filename.split('.')[-1]  # Get file extension
    filename = f'{instance.uuid.hex}.{ext}'  # Generate unique name
    return os.path.join(f'uploads/{instance._meta.model_name}/', filename)


class BaseSpace(AbstractUUIDModel, PolymorphicModel):
    class Type(models.TextChoices):
        FREE = 'FREE', 'Free'
        DISABLED = 'DISABLED', 'Disabled'
        BLUE = 'BLUE', 'Blue'
        GREEN = 'GREEN', 'Green'

    owner = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='spaces')
    type = models.CharField(max_length=10, choices=Type.choices)
    image = models.ImageField(upload_to=unique_upload_path)
    street_name = models.CharField()
    latitude = models.CharField()
    longitude = models.CharField()
    geohash = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    point = models.PointField(geography=True, srid=settings.GEO_SRID, blank=True, null=True, default=None)
    expires_at = models.DateTimeField()

    @property
    def is_expired(self):
        return self.expires_at < timezone.now() - timedelta(minutes=1)

    def expire(self):
        self.expires_at = timezone.now()
        self.save()

    def decrease(self):
        self.expires_at = timezone.now() - timedelta(minutes=15)
        self.save()

    class Queryset(PolymorphicQuerySet):
        def available(self):
            return self.filter(expires_at__gt=timezone.now()).exclude(
                paidspace__reservations__status__in=[
                    Reservation.Status.RESERVED,
                    Reservation.Status.CONFIRMED,
                    Reservation.Status.EXPIRED,
                    Reservation.Status.CANCELLED,
                ]
            )

        def not_reserved(self):
            return self.filter(expires_at__lt=timezone.now()).exclude(
                paidspace__reservations__status__in=[
                    Reservation.Status.RESERVED,
                    Reservation.Status.CONFIRMED,
                    Reservation.Status.CANCELLED,
                ]
            )

        def nearby(self, latitude, longitude, meters=50):
            user_current_point = Point(longitude, latitude, srid=settings.GEO_SRID)
            return (
                self.available()
                .annotate(distance=Distance('point', user_current_point))
                .filter(distance__lt=D(m=meters))
            )

    objects = PolymorphicManager.from_queryset(Queryset)()

    def save(self, *args, **kwargs):
        old = self.__class__.objects.filter(pk=self.pk).last()
        if not self.pk or old and (old.longitude != self.longitude or old.latitude != self.latitude):
            self.point = Point(
                x=float(str(self.longitude)),
                y=float(str(self.latitude)),
            )

        super().save(*args, **kwargs)


class FreeSpace(BaseSpace):
    def __str__(self):
        return f'({self.id}) {self.type}: {self.street_name}'


class SpaceFeedback(AbstractUUIDModel):
    class Type(models.TextChoices):
        TAKE_IT = 'TAKE_IT', 'Take it'
        IN_USE = 'IN_USE', 'In use'
        NOT_USEFUL = 'NOT_USEFUL', 'Not useful'
        PROHIBITED = 'PROHIBITED', 'Prohibited'

    space = models.ForeignKey(BaseSpace, on_delete=models.CASCADE, related_name='feedback')
    reported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=12, choices=Type.choices)

    def __str__(self):
        return f'{self.type}'


class PaidSpace(BaseSpace):
    price = models.IntegerField()
    phone = models.CharField()

    def __str__(self):
        return f'({self.id}) {self.type}: {self.street_name}'

    @property
    def format_price(self):
        return self.price / 100
