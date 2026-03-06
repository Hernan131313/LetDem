from commons.models import AbstractUUIDModel
from commons.utils import calculate_azimuth, global_preferences
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache

from alerts.settings import CACHE_TIMEOUT_FOR_ALERTS


class Alert(AbstractUUIDModel):
    class Type(models.TextChoices):
        RADAR = 'RADAR', 'Radar'
        CAMERA = 'CAMERA', 'Camera'

    class Direction(models.TextChoices):
        CRESCENT = '+', 'Crescent'
        DECREASING = '-', 'Decreasing'
        BOTH = '*', 'Both'

    type = models.CharField(max_length=12, choices=Type.choices)
    direction = models.CharField(max_length=2, choices=Direction.choices)
    latitude = models.CharField()
    longitude = models.CharField()
    point = models.PointField(geography=True, srid=settings.GEO_SRID, blank=True, null=True, default=None)
    road = models.CharField()

    def save(self, *args, **kwargs):
        old = self.__class__.objects.filter(pk=self.pk).last()
        if not self.pk or old and (old.longitude != self.longitude or old.latitude != self.latitude):
            self.point = Point(
                x=float(str(self.longitude)),
                y=float(str(self.latitude)),
            )

        super().save(*args, **kwargs)

    class Queryset(models.QuerySet):
        def nearby(self, latitude: float, longitude: float, meters: int = 50):
            user_current_point = Point(longitude, latitude, srid=settings.GEO_SRID)
            return self.annotate(distance=Distance('point', user_current_point)).filter(distance__lt=D(m=meters))

        def in_front(self, current_point, previous_point: tuple, meters=50, user=None):
            """
            - current (tuple): latitude, longitude
            - previous (tuple): latitude, longitude
            """

            last_location = Point(float(previous_point[1]), float(previous_point[0]), srid=settings.GEO_SRID)
            current_location = Point(float(current_point[1]), float(current_point[0]), srid=settings.GEO_SRID)

            alerts = []
            azimuth_user = calculate_azimuth(last_location, current_location)
            nearby_alerts = self.nearby(float(current_point[0]), float(current_point[1]), meters)
            for nearby_alert in nearby_alerts:
                redis_key = f'{nearby_alert.uuid.hex}.{user.uuid.hex}'
                if cache.get(redis_key):
                    continue

                cache_timeout = global_preferences[CACHE_TIMEOUT_FOR_ALERTS]
                cache.set(redis_key, '+', timeout=cache_timeout)

                azimuth_alert = calculate_azimuth(current_location, nearby_alert.point)
                delta = (azimuth_alert - azimuth_user + 360) % 360
                if (0 < delta <= 180) and nearby_alert.direction == '+':
                    alerts.append(nearby_alert)
                elif nearby_alert.direction == '-':
                    alerts.append(nearby_alert)

            return alerts

    objects = models.Manager.from_queryset(Queryset)()

    class Meta:
        ordering = ('type', 'road')

    def __str__(self):
        return f'{self.type} - {self.road} ({self.direction})'


class LowEmissionZone(AbstractUUIDModel):
    city = models.CharField()
    polygon = models.PolygonField(srid=settings.GEO_SRID)
    restrictions = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f'LEZ: {self.city}'
