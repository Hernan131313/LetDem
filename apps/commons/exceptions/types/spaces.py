from django.utils.translation import gettext_lazy as _

from commons.exceptions.base import APIBaseException


class SpacePublishedNearByRecently(APIBaseException):
    detail = _('Space Published Nearby Recently.')
    error_code = 'SPACE_PUBLISHED_NEARBY_RECENTLY'


class SpaceNotFound(APIBaseException):
    detail = _('Space not found.')
    error_code = 'SPACE_NOT_FUND'


class SpaceFeedbackAlreadyCreated(APIBaseException):
    detail = _('Space feedback already created.')
    error_code = 'SPACE_FEEDBACK_ALREADY_CREATED'


class SpaceOwnerCanNotSendFeedback(APIBaseException):
    detail = _('Space owner cannot send feedback.')
    error_code = 'SPACE_OWNER_CANNOT_SEND_FEEDBACK'


class SpaceInvalidPrice(APIBaseException):
    detail = _('Space price should be higher than 3.')
    error_code = 'SPACE_INVALID_PRICE'


class SpaceInvalidTimeToWait(APIBaseException):
    detail = _('Space time_to_wait should be higher in range of 20 - 60 minutes.')
    error_code = 'SPACE_INVALID_TIME_TO_WAIT'
