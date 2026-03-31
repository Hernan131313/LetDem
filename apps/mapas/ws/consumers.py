import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django_redis import get_redis_connection

from maps.ws.events.registry import EVENTS_REGISTRY


class MapsConsumer(AsyncJsonWebsocketConsumer):
    cache_key = 'letdem:ws:region:{}'
    cache = get_redis_connection('default')

    async def connect(self):
        self.region = 'letdem.noreqion'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """
        Example event data
        {
            'event_type': 'update.live.location',
            'data': {
               'lat': 40.90320393390,
               'lng': -3.90894389444
            }
        }
        """
        from maps.ws.filters import retrieve_map_data

        event_data = json.loads(text_data)
        if 'event_type' not in event_data or 'data' not in event_data:
            error_message = {
                'error-code': 'invalid-payload',
                'message': "'event_type' and 'data' are required to send event to server",
            }
            await self.send_json(error_message, close=True)

        event_type = event_data['event_type']
        if event_type not in EVENTS_REGISTRY:
            error_message = {
                'error-code': 'invalid-event',
                'message': f'event_type ({event_type}) is not a valid event',
            }
            await self.send_json(error_message, close=True)

        await EVENTS_REGISTRY[event_type](self, event_data['data'])

        response_data = await sync_to_async(retrieve_map_data)(self.user, self.region)
        await self.send_json(response_data)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.region, self.channel_name)

    async def on_maps_update(self, _):
        from maps.ws.filters import retrieve_map_data

        response_data = await sync_to_async(retrieve_map_data)(self.user, self.region)
        await self.send_json(response_data)

    async def add_user_to_group(self, region):
        self.cache.sadd(self.cache_key.format(region), self.channel_name)

    async def remove_user_from_group(self, region):
        self.cache.srem(self.cache_key.format(region), self.channel_name)
