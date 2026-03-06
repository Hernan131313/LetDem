from django.urls import path, re_path

from spaces.v1 import views

urlpatterns = [
    path('free', views.CreateFreeSpaceAPIView.as_view(), name='create-free-spaces'),
    path('paid', views.CreatePaidSpaceAPIView.as_view(), name='create-paid-spaces'),
    re_path('(?P<uuid>[0-9a-fA-F]{32})$', views.RetrieveDeleteSpaceAPIView.as_view(), name='retrieve-delete-space'),
    re_path('(?P<uuid>[0-9a-fA-F]{32})/feedback$', views.CreateSpaceFeedbackAPIView.as_view(), name='space-feedback'),
    re_path('(?P<uuid>[0-9a-fA-F]{32})/reserve$', views.ReserveSpaceAPIView.as_view(), name='reserve-space'),
    re_path(
        '(?P<uuid>[0-9a-fA-F]{32})/extend-expiration$',
        views.ExtendSpaceExpirationAPIView.as_view(),
        name='extend-space-expiration',
    ),
    re_path(
        '(?P<uuid>[0-9a-fA-F]{32})/confirm-reservation',
        views.ConfirmReservationSpaceAPIView.as_view(),
        name='confirm-space',
    ),
]
