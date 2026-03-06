from django.urls import re_path

from . import consumers

ws_urls = [
    re_path(r'ws/maps/nearby$', consumers.MapsConsumer.as_asgi()),
]
