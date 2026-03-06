"""
ASGI config for letdem project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'letdem.settings.local')
django.setup()

from commons.ws.middlewares import TokenAuthMiddleware  # noqa
from maps.ws.routing import ws_urls as maps_ws_urls  # noqa
from accounts.modules.users.ws.routing import ws_urls as users_ws_urls  # noqa

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.

websocket_urlpatterns = maps_ws_urls + users_ws_urls

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
