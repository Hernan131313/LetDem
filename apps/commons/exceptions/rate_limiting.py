from commons.exceptions.base import APIBaseException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class ResendMaxLimit(APIBaseException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = _('Resend Max Limit Reached.')
    error_code = 'RESEND_MAX_LIMIT'
