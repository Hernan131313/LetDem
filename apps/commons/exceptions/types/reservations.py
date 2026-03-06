from django.utils.translation import gettext_lazy as _

from commons.exceptions.base import APIBaseException


class SpaceAlreadyReserved(APIBaseException):
    detail = _('Space Already Reserved.')
    error_code = 'SPACE_ALREADY_RESERVED'


class SpaceOwnerCannotReserve(APIBaseException):
    detail = _('Space Owner Cannot Reserve.')
    error_code = 'SPACE_OWNER_CANNOT_RESERVE'


class ReservationNotFound(APIBaseException):
    detail = _('Reservation Not Found')
    error_code = 'RESERVATION_NOT_FOUND'


class InvalidConfirmationCode(APIBaseException):
    detail = _('Invalid Confirmation Code')
    error_code = 'INVALID_CONFIRMATION_CODE'


class ConfirmReservationError(APIBaseException):
    detail = _('Confirm Reservation Error')
    error_code = 'CONFIRM_RESERVATION_ERROR'


class CancelReservationError(APIBaseException):
    detail = _('Cancel Reservation Error')
    error_code = 'CANCEL_RESERVATION_ERROR'


class ReservationCancelledError(APIBaseException):
    detail = _('This reservation has been cancelled')
    error_code = 'RESERVATION_CANCELLED'


class ActiveReservationAlreadyExist(APIBaseException):
    detail = _('Active Reservation Already Exist.')
    error_code = 'ACTIVE_RESERVATION_ALREADY_EXIST'
