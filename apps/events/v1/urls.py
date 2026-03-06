from django.urls import path, re_path

from events.v1 import views

urlpatterns = [
    path('', views.CreateEventAPIView.as_view(), name='create-event'),
    re_path('/(?P<uuid>[0-9a-fA-F]{32})/feedback$', views.CreateEventFeedbackAPIView.as_view(), name='event_feedback'),
]
