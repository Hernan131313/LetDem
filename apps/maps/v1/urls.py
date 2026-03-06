from django.urls import path

from maps.v1 import views

urlpatterns = [
    path('nearby', views.MapsNearbyAPIView.as_view(), name='maps-nearby'),
    path('routes', views.MapsRoutesAPIView.as_view(), name='maps-routes'),
]
