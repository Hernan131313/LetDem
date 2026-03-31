from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.dispatch import Signal, receiver

refresh_maps = Signal()


@receiver(refresh_maps)
def refresh_maps_handler(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(instance.geohash, {'type': 'on_maps_update', 'data': {}})
