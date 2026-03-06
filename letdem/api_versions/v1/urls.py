from django.urls import include, path

urlpatterns = [
    path('auth/', include('accounts.modules.auth.v1.urls')),
    path('users/', include('accounts.modules.users.v1.urls')),
    path('spaces/', include('spaces.v1.urls')),
    path('maps/', include('maps.v1.urls')),
    path('credits/', include('credits.v1.urls')),
    path('reservations/', include('reservations.v1.urls')),
    path('events', include('events.v1.urls')),
    path('marketplace/', include('marketplace.v1.urls')),
]
