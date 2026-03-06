from django.utils.translation import gettext_lazy as _

from commons.exceptions.base import APIBaseException


class EarningAccountAlreadyExists(APIBaseException):
    detail = _('Earning Account Already Exists.')
    error_code = 'EARNING_ACCOUNT_ALREADY_EXISTS'


class EarningAccountIsRequired(APIBaseException):
    detail = _('Earning Account Is Required.')
    error_code = 'EARNING_ACCOUNT_REQUIRED'


class EarningAccountIsNotAccepted(APIBaseException):
    detail = _('Earning Account Is Not Accepted.')
    error_code = 'EARNING_ACCOUNT_IS_NOT_ACCEPTED'


class CountryNotSupported(APIBaseException):
    detail = _('Country not supported.')
    error_code = 'COUNTRY_NOT_SUPPORTED'


class BadRequestForCurrentStep(APIBaseException):
    detail = _('Bad Request for current step.')
    error_code = 'BAD_REQUEST_FOR_CURRENT_STEP'


class InvalidAddressCountry(APIBaseException):
    detail = _('Account country must be equals to address country.')
    error_code = 'INVALID_ADDRESS_COUNTRY'


class InvalidPayoutMethodForAccountCountry(APIBaseException):
    detail = _('Invalid Payout Method for account country.')
    error_code = 'INVALID_PAYOUT_METHOD_FOR_ACCOUNT_COUNTRY'


class PaymentMethodNotFound(APIBaseException):
    detail = _('Payment Method Not Found')
    error_code = 'PAYMENT_METHOD_NOT_FOUND'


class PaymentMethodAlreadyExists(APIBaseException):
    detail = _('Payment Method Already Exists')
    error_code = 'PAYMENT_METHOD_ALREADY_EXISTS'


class BalanceLowerThanTheMinimum(APIBaseException):
    detail = _('Balance Lower Than Minimum to Withdraw')
    error_code = 'BALANCE_LOWER_THAN_MINIMUM'


class PayoutMethodNotFound(APIBaseException):
    detail = _('Payout Method Not Found')
    error_code = 'PAYOUT_METHOD_NOT_FOUND'


class PayoutRequestFailed(APIBaseException):
    detail = _('Payout Request Failed')
    error_code = 'PAYOUT_REQUEST_FAILED'
