from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django_redis import get_redis_connection


class RefreshUserConsumer(AsyncJsonWebsocketConsumer):
    cache_key = 'letdem:ws:region:{}'
    cache = get_redis_connection('default')

    async def connect(self):
        self.region = 'letdem.noreqion'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f'users_{self.user.uuid.hex}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        await self.send_json({'event_type': {}})

    async def refresh_user(self, event):
        await self.send_json(
            {
                'event_type': 'refresh_user',
                **(event.get('payload') or {}),
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
