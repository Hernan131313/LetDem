from rest_framework.views import exception_handler
from rest_framework.response import Response
from commons.exceptions.base import APIBaseException


def api_exception_handler(exc, context):
    # You can handle different types of exceptions here
    response = exception_handler(exc, context)

    if issubclass(exc.__class__, APIBaseException):
        return Response(
            data={'error_code': exc.error_code, 'message': exc.detail},
            status=exc.status_code,
        )

    return response
