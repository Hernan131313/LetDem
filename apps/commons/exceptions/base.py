from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class APIBaseException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = _('Invalid Request.')
    error_code = 'error'

    def __init__(self, detail=None, code=None):
        if detail is not None:
            self.detail = detail

        if code is not None:
            self.error_code = code


class InvalidCoordinates(APIBaseException):
    detail = _('Invalid coordinates has been provided.')
    error_code = 'INVALID_COORDINATES'


class InvalidPhoneNumber(APIBaseException):
    detail = _('Phone is invalid.')
    error_code = 'INVALID_PHONE'


class EighteenYearsRequired(APIBaseException):
    detail = _('Customer must have 18 years at least.')
    error_code = 'EIGHTEEN_YEARS_REQUIRED'
