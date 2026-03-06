from django.utils.translation import gettext_lazy as _

from commons.exceptions.base import APIBaseException


class EventPublicationError(APIBaseException):
    detail = _('Event publication Error.')
    error_code = 'EVENT_PUBLICATION_ERROR'


class EventNotFound(APIBaseException):
    detail = _('Event not found.')
    error_code = 'EVENT_NOT_FUND'


class EventFeedbackAlreadyCreated(APIBaseException):
    detail = _('Event feedback already created.')
    error_code = 'EVENT_FEEDBACK_ALREADY_CREATED'


class EventOwnerCanNotSendFeedback(APIBaseException):
    detail = _('Event owner cannot send feedback.')
    error_code = 'EVENT_OWNER_CANNOT_SEND_FEEDBACK'
