from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user(token):
    try:
        return Token.objects.get(key=token).user
    except Exception:
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Custom ASGI middleware for DRF Token authentication over WebSocket.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        token = parse_qs(query_string).get('token', [None])[0]

        scope['user'] = await get_user(token) if token else AnonymousUser()

        return await self.app(scope, receive, send)
