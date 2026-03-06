from functools import wraps

import stripe
from rest_framework.exceptions import ValidationError


def _process_exception_data(exception: stripe.error.StripeError):
    return {
        'type': exception.error.type,
        'code': exception.error.code or '',
        'param': exception.error.param or '',
        'message': exception.error.message,
    }


def handle_stripe_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except stripe.error.CardError as e:
            raise ValidationError(_process_exception_data(e))
        except stripe.error.RateLimitError as e:
            raise ValidationError(_process_exception_data(e))
        except stripe.error.InvalidRequestError as e:
            raise ValidationError(_process_exception_data(e))
        except stripe.error.StripeError as e:
            raise ValidationError(_process_exception_data(e))

    return wrapper
