from django.utils.translation import gettext_lazy as _
from rest_framework import status

from commons.exceptions.base import APIBaseException


class EmptyCart(APIBaseException):
    detail = _('The order must contain at least one item.')
    error_code = 'MARKETPLACE_EMPTY_CART'


class ProductNotFound(APIBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = _('One or more products were not found or are inactive.')
    error_code = 'MARKETPLACE_PRODUCT_NOT_FOUND'


class InsufficientStock(APIBaseException):
    detail = _('There is not enough stock for one or more products.')
    error_code = 'MARKETPLACE_INSUFFICIENT_STOCK'


class InsufficientPoints(APIBaseException):
    detail = _('You do not have enough points to complete this action.')
    error_code = 'MARKETPLACE_INSUFFICIENT_POINTS'


class InvalidOrderItem(APIBaseException):
    detail = _('Order items must include the product and quantity.')
    error_code = 'MARKETPLACE_INVALID_ORDER_ITEM'
