from django.urls import path, re_path

from accounts.modules.users.v1 import views

urlpatterns = [
    path('me', views.UserMeAPIView.as_view(), name='me'),
    path('me/change-password', views.ChangePasswordAPIView.as_view(), name='change-password'),
    path('me/change-language', views.ChangeUserLanguageAPIView.as_view(), name='change-password'),
    path('me/update-device-id', views.UpdateDeviceIdAPIView.as_view(), name='update-device-id'),
    path('me/delete-account', views.DeleteAccountAPIView.as_view(), name='delete-account'),
    path('me/car', views.CarAPIView.as_view(), name='car'),
    path('me/car/parked-place', views.CarParkedPlaceAddressAPIView.as_view(), name='car-park'),
    path('me/addresses/home', views.HomeAddressAPIView.as_view(), name='addresses-home'),
    path('me/addresses/work', views.WorkAddressAPIView.as_view(), name='addresses-work'),
    path('me/addresses', views.FavoritesAddressAPIView.as_view(), name='addresses-list'),
    path('me/contributions', views.ContributionsListAPIView.as_view(), name='contributions-list'),
    path('me/preferences', views.UserPreferencesAPIView.as_view(), name='preferences'),
    path(
        'me/scheduled-notifications',
        views.ScheduledNotificationAPIView.as_view(),
        name='create-list-scheduled-notifications',
    ),
    re_path(
        'me/scheduled-notifications/(?P<uuid>[0-9a-fA-F]{32})$',
        views.ScheduledNotificationAPIView.as_view(),
        name='update-scheduled-notifications',
    ),
    re_path(
        'me/notifications$',
        views.NotificationsListDeleteAllAPIView.as_view(),
        name='notifications-list-delete-all',
    ),
    re_path(
        'me/notifications/(?P<uuid>[0-9a-fA-F]{32})/read$',
        views.NotificationReadAPIView.as_view(),
        name='notification-read',
    ),
]
