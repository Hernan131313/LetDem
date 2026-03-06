from datetime import timedelta

from commons.models import AbstractUUIDModel
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone


class Event(AbstractUUIDModel):
    class Type(models.TextChoices):
        ACCIDENT = 'ACCIDENT', 'Accident'
        POLICE = 'POLICE', 'Police'
        CLOSED_ROAD = 'CLOSED_ROAD', 'Closed Road'

    owner = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    type = models.CharField(max_length=12, choices=Type.choices)
    street_name = models.CharField()
    latitude = models.CharField()
    longitude = models.CharField()
    geohash = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    point = models.PointField(geography=True, srid=settings.GEO_SRID, blank=True, null=True, default=None)
    expires_at = models.DateTimeField()

    @property
    def contribution_received(self):
        metadata = self.metadata or {}
        return metadata.get('contribution_created')

    def increase_time(self):
        self.expires_at = timezone.now() + timedelta(minutes=30)
        self.save()

    def decrease_time(self):
        self.expires_at = timezone.now() - timedelta(minutes=15)
        self.save()

    @property
    def is_expired(self):
        return self.expires_at < timezone.now()

    def save(self, *args, **kwargs):
        old = self.__class__.objects.filter(pk=self.pk).last()
        if not self.pk or old and (old.longitude != self.longitude or old.latitude != self.latitude):
            self.point = Point(
                x=float(str(self.longitude)),
                y=float(str(self.latitude)),
            )

        super().save(*args, **kwargs)

    class Queryset(models.QuerySet):
        def available(self):
            return self.filter(expires_at__gt=timezone.now())

        def nearby(self, latitude, longitude, meters=50):
            user_current_point = Point(longitude, latitude, srid=settings.GEO_SRID)
            return (
                self.available()
                .annotate(distance=Distance('point', user_current_point))
                .filter(distance__lt=D(m=meters))
            )

    objects = models.Manager.from_queryset(Queryset)()

    def __str__(self):
        return f'{self.type} - {self.street_name}'


class EventFeedback(AbstractUUIDModel):
    class Type(models.TextChoices):
        IS_THERE = 'IS_THERE', 'It is there'
        NOT_THERE = 'NOT_THERE', 'It is not there'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    reported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=12, choices=Type.choices)

    def __str__(self):
        return f'{self.type}'
