from django.urls import re_path

from reservations.v1 import views

urlpatterns = [
    re_path(
        '(?P<uuid>[0-9a-fA-F]{32})/confirm',
        views.ConfirmReservationAPIView.as_view(),
        name='confirm-reservation',
    ),
    re_path(
        '(?P<uuid>[0-9a-fA-F]{32})/cancel',
        views.CancelReservationAPIView.as_view(),
        name='cancel-reservation',
    ),
]
