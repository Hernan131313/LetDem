from accounts.models import User
from celery import shared_task
from commons.push_notifications.onesignal.handlers import send_push_notification
from commons.push_notifications.onesignal.settings import ACCOUNT_ACCEPTED_NOTIFICATION


@shared_task
def send_notification_earning_account_accepted_task(user_id):
    """
    notify users that his earning account is approved.
    """
    user: User = User.objects.filter(id=user_id).last()
    if not user:
        return

    for user_device in user.user_devices.all():
        if not user.user_preferences.push:
            break

        device_id = user_device.device_id
        notification_data = {'page_to_redirect': 'wallet'}
        send_push_notification(
            device_id, notification_type=ACCOUNT_ACCEPTED_NOTIFICATION, notification_data=notification_data, params={}
        )
