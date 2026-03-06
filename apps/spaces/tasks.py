from io import BytesIO

from accounts.models import Notification, ScheduledNotification
from celery import shared_task
from commons.push_notifications.onesignal import settings as onesignal_settings
from commons.push_notifications.onesignal.handlers import send_push_notification
from commons.push_notifications.onesignal.settings import SPACE_ABOUT_TO_EXPIRE, SPACE_RESERVED_NOTIFICATION
from commons.utils import global_preferences, send_refresh_users_event
from django.core.files.base import ContentFile
from PIL import Image

from spaces import settings
from spaces.models import BaseSpace


@shared_task
def compress_image_task(instance_pk, field_name='image', max_size=(800, 800), quality=85):
    """
    Compress the image stored in the given model instance's ImageField.

    :param instance_pk: The model instance pk
    :param field_name: The name of the ImageField (default is 'image')
    :param max_size: Maximum width and height for the thumbnail
    :param quality: JPEG quality for the compressed image
    """

    instance = BaseSpace.objects.filter(pk=instance_pk).last()
    # Retrieve the file from the ImageField
    image_field = getattr(instance, field_name)
    if not image_field:
        return

    # Open the image (this works with S3 storage as well)
    image_field.open()
    try:
        with Image.open(image_field) as img:
            img = img.convert('RGB')
            # Create a thumbnail (resize in-place)
            img.thumbnail(max_size)

            # Save the compressed image into an in-memory stream
            output_stream = BytesIO()
            img.save(output_stream, format='png', optimize=True, quality=quality)
            output_stream.seek(0)
    except Exception:
        return

    # Replace the current image with the compressed image
    image_field.save(image_field.name, ContentFile(output_stream.read(), name=image_field.name), save=False)
    instance.save()


@shared_task
def send_notification_for_scheduled_places(space_id):
    """
    notify users that has scheduled notifications in some places.
    """
    space: BaseSpace = BaseSpace.objects.filter(uuid=space_id).last()
    if not space:
        return

    radius = global_preferences[settings.MAX_RADIUS_FOR_SCHEDULED_NOTIFICATIONS]
    latitude, longitude = float(space.latitude), float(space.longitude)
    scheduled_notifications = ScheduledNotification.objects.nearby(latitude, longitude, radius)
    for scheduled_notification in scheduled_notifications:
        user = scheduled_notification.user
        if scheduled_notification.radius < scheduled_notification.distance.m:
            continue

        if not user.user_preferences.available_spaces:
            continue

        Notification.objects.create(
            user=scheduled_notification.user, type=Notification.Type.SPACE_NEARBY, content_object=space
        )

        for user_device in user.user_devices.all():
            if not user.user_preferences.push:
                break

            device_id = user_device.device_id
            meters = int(scheduled_notification.distance.m)
            params = {'meters': meters, 'street_name': scheduled_notification.street_name}
            notification_data = {'page_to_redirect': 'destination_route', 'space_id': space_id}
            send_push_notification(
                device_id,
                notification_type=onesignal_settings.SPACE_SCHEDULED_IN_PLACE_NOTIFICATION,
                notification_data=notification_data,
                params=params,
            )


@shared_task
def send_notification_for_space_occupied(space_id: str, points: int):
    """
    notify users that has been occupied.
    """
    space: BaseSpace = BaseSpace.objects.filter(uuid=space_id).last()
    if not space:
        return

    Notification.objects.create(user=space.owner, type=Notification.Type.SPACE_OCCUPIED, content_object=space)

    user = space.owner
    for user_device in user.user_devices.all():
        if not user.user_preferences.push:
            break

        device_id = user_device.device_id
        params = {'street_name': space.street_name, 'points': points}
        notification_data = {'page_to_redirect': 'contributions'}
        send_push_notification(
            device_id,
            notification_type=onesignal_settings.SPACE_OCCUPIED_NOTIFICATION,
            notification_data=notification_data,
            params=params,
        )


@shared_task
def send_space_reserved_notification_task(space_uuid):
    """
    notify users that his space has been reserved.
    """
    from maps.signals import refresh_maps

    space: BaseSpace = BaseSpace.objects.filter(uuid=space_uuid).last()
    if not space:
        return

    refresh_maps.send(None, instance=space)

    Notification.objects.create(user=space.owner, type=Notification.Type.SPACE_RESERVED, content_object=space)

    user = space.owner
    for user_device in user.user_devices.all():
        if not user.user_preferences.push:
            break

        device_id = user_device.device_id
        notification_data = {'page_to_redirect': 'reservation_details'}
        send_push_notification(
            device_id, notification_type=SPACE_RESERVED_NOTIFICATION, notification_data=notification_data, params={}
        )


@shared_task
def remind_space_about_to_expire_notification_task(space_id: int):
    """
    Notify user that his space will expire soon.
    """

    space = BaseSpace.objects.available().filter(id=space_id).last()
    if not space:
        return

    user = space.owner
    minutes_before_to_notify = global_preferences[settings.MINUTES_BEFORE_SPACE_EXPIRATION]
    notification_data = {'page_to_redirect': 'reservation_details'}

    for user_device in user.user_devices.all():
        if not user.user_preferences.push:
            break

        device_id = user_device.device_id

        send_push_notification(
            device_id,
            notification_type=SPACE_ABOUT_TO_EXPIRE,
            notification_data=notification_data,
            params={'minutes': minutes_before_to_notify},
        )


@shared_task
def space_has_been_expired(space_id: int):
    from maps.signals import refresh_maps

    space: BaseSpace = BaseSpace.objects.filter(id=space_id).last()
    if not space or not space.is_expired:
        return

    send_refresh_users_event(users=[space.owner])
    refresh_maps.send(None, instance=space)
