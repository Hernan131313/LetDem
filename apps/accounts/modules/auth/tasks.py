from celery import shared_task
from commons.utils import generate_six_digits_otp, hash_otp, send_email
from django.conf import settings
from django.core.cache import cache
from django.utils import translation
from django.utils.translation import gettext as _

from accounts.models import ResetPasswordRequestOTP, User, UserDevice


@shared_task
def send_email_verification_task(user_id):
    user = User.objects.filter(id=user_id).last()
    key = f'email_verification__{user.uuid.hex}'

    if cache.get(key):
        cache.delete(key)

    generated_code = generate_six_digits_otp()
    hashed_otp = hash_otp(str(generated_code))
    expiration_in_seconds = int(settings.VALIDATION_CODE_EXPIRE_TIME)
    cache.set(key, hashed_otp, timeout=expiration_in_seconds)
    with translation.override(user.language):
        send_email(
            to_emails=[user.email],
            subject=_('Confirm your email'),
            template=f'auth/{user.language}/email_verification',
            context={'verification_code': generated_code, 'expiration_in_minutes': int(expiration_in_seconds / 60)},
        )


@shared_task
def reset_password_email_task(user_id):
    user = User.objects.filter(id=user_id).last()
    generated_code = generate_six_digits_otp()
    expiration_in_seconds = int(settings.VALIDATION_CODE_EXPIRE_TIME)
    otp_hashed = hash_otp(str(generated_code))
    ResetPasswordRequestOTP.objects.create(user=user, otp_hashed=otp_hashed)
    with translation.override(user.language):
        send_email(
            to_emails=[user.email],
            subject=_('Reset Password'),
            template=f'auth/{user.language}/email_reset_password',
            context={'verification_code': generated_code, 'expiration_in_minutes': int(expiration_in_seconds / 60)},
        )


@shared_task
def create_user_device_task(user_id, device_id):
    user = User.objects.get(id=user_id)
    UserDevice.objects.filter(device_id=device_id).delete()
    UserDevice.objects.create(user=user, device_id=device_id)
