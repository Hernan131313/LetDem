from django.utils.translation import gettext_lazy as _
from rest_framework import status

from commons.exceptions.base import APIBaseException


class InvalidCredentials(APIBaseException):
    detail = _('Invalid Credentials.')
    error_code = 'INVALID_CREDENTIALS'


class InvalidCurrentPassword(APIBaseException):
    detail = _('Invalid Current Password.')
    error_code = 'INVALID_CURRENT_PASSWORD'


class RepeatedPassword(APIBaseException):
    detail = _('Repeated Password.')
    error_code = 'REPEATED_PASSWORD'


class InactiveAccount(APIBaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = _('Inactive Account.')
    error_code = 'INACTIVE_ACCOUNT'


class EmailAlreadyExists(APIBaseException):
    detail = _('Email Already Exists.')
    error_code = 'EMAIL_ALREADY_EXISTS'


class InvalidSocialToken(APIBaseException):
    detail = _('Invalid Social Token.')
    error_code = 'INVALID_SOCIAL_TOKEN'


class InvalidOTP(APIBaseException):
    detail = _('Invalid OTP.')
    error_code = 'INVALID_OTP'


class AccountAlreadyActivated(APIBaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = _('Account Already Activated.')
    error_code = 'ACCOUNT_ALREADY_ACTIVATED'


class EmailNotFound(APIBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = _('This email does not exist in our system.')
    error_code = 'EMAIL_NOT_FOUND'


class OTPNotValidated(APIBaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = _('OTP related to this operation is not validated.')
    error_code = 'OTP_NOT_VALIDATED'


class CarAlreadyCreated(APIBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = _('This user already has created a car.')
    error_code = 'CAR_ALREADY_CREATED'


class UserDoesNotHaveCar(APIBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = _('User does not have a car created.')
    error_code = 'USER_DOES_NOT_HAVE_CAR'


class SocialUserCannotResetPassword(APIBaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = _('Social user should reset password through its provider')
    error_code = 'SOCIAL_USER_CANNOT_RESET_PASSWORD'


class EndsAndStartsTimeShouldBeGreater(APIBaseException):
    detail = _('Ends time should be greater than Starts time')
    error_code = 'ENDS_TIME_SHOULD_BE_GREATER'


class EndsAndStartsTimeShouldBeGreaterThanNow(APIBaseException):
    detail = _('Ends and Starts time should be greater than now')
    error_code = 'ENDS_AND_START_TIME_SHOULD_BE_GREATER_THAN_NOW'


class NotificationAlreadyScheduledInPlace(APIBaseException):
    detail = _('Notification already scheduled in this place')
    error_code = 'NOTIFICATION_ALREADY_SCHEDULED_IN_PLACE'
