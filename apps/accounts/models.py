from datetime import timedelta

from commons.models import AbstractUUIDModel
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone

from accounts.managers import StaffUserManager, UserManager


class User(AbstractUser, AbstractUUIDModel):
    class Languages(models.TextChoices):
        SPANISH = 'es', 'Spanish'
        ENGLISH = 'en', 'English'

    username = None
    email = models.EmailField(unique=True, db_index=True)
    social_id = models.CharField(max_length=2000, null=True, blank=True)
    total_points = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=2, choices=Languages.choices, default='en')
    provider_customer_id = models.CharField(max_length=250, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_social(self):
        return self.social_id is not None

    @property
    def has_earning_account(self):
        return hasattr(self, 'earning_account') and self.earning_account is not None

    @property
    def has_accepted_account(self):
        return self.has_earning_account and self.earning_account.is_accepted


class StaffUser(User):
    objects = StaffUserManager()

    class Meta:
        proxy = True
        verbose_name = 'Staff User'
        verbose_name_plural = 'Staff Users'
        ordering = ['-created']


class UserDevice(AbstractUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_devices')
    device_id = models.CharField()

    def __str__(self):
        return f'{self.user} - {self.device_id}'


class UserPreferences(AbstractUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_preferences')
    available_spaces = models.BooleanField(default=True)
    radar_alert = models.BooleanField(default=True)
    camera_alert = models.BooleanField(default=True)
    prohibited_zone_alert = models.BooleanField(default=True)
    speed_limit_alert = models.BooleanField(default=True)
    fatigue_alert = models.BooleanField(default=True)
    police_alert = models.BooleanField(default=True)
    accident_alert = models.BooleanField(default=True)
    road_closed_alert = models.BooleanField(default=True)
    email = models.BooleanField(default=True)
    push = models.BooleanField(default=True)

    def __str__(self):
        return f'Preferences: {self.user}'


class ResetPasswordRequestOTP(AbstractUUIDModel):
    user = models.ForeignKey('User', related_name='reset_password_requests', on_delete=models.CASCADE)
    is_validated = models.BooleanField(default=False)
    otp_hashed = models.CharField(max_length=70)

    class Queryset(models.QuerySet):
        def ontime(self):
            last_validation = timezone.now() - timedelta(seconds=int(settings.VALIDATION_CODE_EXPIRE_TIME))
            return self.filter(created__gt=last_validation)

        def validate(self):
            self.ontime().update(is_validated=True)

        def is_validated(self):
            return self.ontime().filter(is_validated=True).exists()

    objects = models.Manager.from_queryset(Queryset)()


class CarParkedPlace(AbstractUUIDModel):
    car = models.OneToOneField('Car', on_delete=models.CASCADE, related_name='parked_place')
    street_name = models.CharField()
    latitude = models.CharField()
    longitude = models.CharField()

    def __str__(self):
        return f'{self.street_name} ({self.latitude}, {self.longitude})'


class Car(AbstractUUIDModel):
    class Label(models.TextChoices):
        ZERO = 'ZERO', 'Zero'
        ECO = 'ECO', 'Eco'
        B = 'B', 'B'
        C = 'C', 'C'
        NONE = 'NONE', 'None'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='car')
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=5, choices=Label.choices)
    plate_number = models.CharField(max_length=15)

    def __str__(self):
        return f'{self.name} - {self.plate_number}'

    def update_last_parked_place(self, space):
        CarParkedPlace.objects.update_or_create(
            car=self,
            defaults={
                'street_name': space.street_name,
                'latitude': space.latitude,
                'longitude': space.longitude,
            },
        )


class FavoriteAddress(AbstractUUIDModel):
    class Type(models.TextChoices):
        HOME = 'HOME', 'Home'
        WORK = 'WORK', 'Work'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    type = models.CharField(max_length=4, choices=Type.choices)
    street_name = models.CharField()
    latitude = models.CharField()
    longitude = models.CharField()

    class Queryset(models.QuerySet):
        def home(self):
            return self.filter(type=self.model.Type.HOME)

        def work(self):
            return self.filter(type=self.model.Type.WORK)

    objects = models.Manager.from_queryset(Queryset)()

    class Meta:
        ordering = ['type']


class Contribution(AbstractUUIDModel):
    class Type(models.TextChoices):
        SPACE = 'SPACE', 'Space'
        EVENT = 'EVENT', 'Event'

    class Action(models.TextChoices):
        SPACE_CREATED = 'SPACE_CREATED', 'Space created'
        SPACE_OCCUPIED = 'SPACE_OCCUPIED', 'Space occupied'
        SPACE_NOT_VALID = 'SPACE_NOT_VALID', 'Space not valid'
        SPACE_IN_USE = 'SPACE_IN_USE', 'Space in use'

        EVENT_CREATED = 'EVENT_CREATED', 'Event created'
        EVENT_POLICE = 'POLICE', 'Event police'
        EVENT_ROAD_CLOSED = 'CLOSED_ROAD', 'Event closed road'
        EVENT_ACCIDENT = 'ACCIDENT', 'Event accident'

        FEEDBACK = 'FEEDBACK', 'User feedback'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    type = models.CharField(max_length=5, choices=Type.choices)
    action = models.CharField(max_length=20, choices=Action.choices)
    points = models.PositiveSmallIntegerField()

    class Queryset(models.QuerySet):
        def spaces(self):
            return self.filter(type=self.model.Type.SPACE)

        def events(self):
            return self.filter(type=self.model.Type.EVENT)

        def recents(self):
            return self.all()[:5]

    objects = models.Manager.from_queryset(Queryset)()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.type} - {self.action}'


class ScheduledNotification(AbstractUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_notifications')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    radius = models.FloatField()
    street_name = models.CharField()
    latitude = models.CharField()
    longitude = models.CharField()
    point = models.PointField(geography=True, srid=settings.GEO_SRID, blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        old = self.__class__.objects.filter(pk=self.pk).last()
        if not self.pk or old and (old.longitude != self.longitude or old.latitude != self.latitude):
            self.point = Point(
                x=float(str(self.longitude)),
                y=float(str(self.latitude)),
            )

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.ends_at

    class Queryset(models.QuerySet):
        def active(self):
            return self.filter(ends_at__gt=timezone.now())

        def nearby(self, latitude, longitude, meters=1000):
            space_location_point = Point(longitude, latitude, srid=settings.GEO_SRID)
            return (
                self.active()
                .annotate(distance=Distance('point', space_location_point))
                .filter(distance__lt=D(m=meters))
            )

    objects = models.Manager.from_queryset(Queryset)()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.street_name} - ({self.starts_at} - {self.ends_at})'


class Notification(AbstractUUIDModel):
    class Type(models.TextChoices):
        SPACE_OCCUPIED = 'SPACE_OCCUPIED', 'Space occupied'
        SPACE_RESERVED = 'SPACE_RESERVED', 'Space reserved'
        SPACE_NEARBY = 'SPACE_NEARBY', 'Space nearby'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    read = models.BooleanField(default=False)
    type = models.CharField(max_length=15, choices=Type.choices)

    class Queryset(models.QuerySet):
        def unread(self):
            return self.filter(read=False)

        def read(self):
            return self.filter(read=True)

    objects = models.Manager.from_queryset(Queryset)()

    def __str__(self):
        return f'{self.type} - {"read" if self.read else "unread"}'
