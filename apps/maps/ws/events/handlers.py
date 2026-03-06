from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from commons.utils import generate_coordinates_geohash

if TYPE_CHECKING:
    from maps.ws.consumers import MapsConsumer


async def update_live_location_event(_self: 'MapsConsumer', event_data: dict):
    latitude, longitude = str(event_data['lat']), str(event_data['lat'])
    new_region = await sync_to_async(generate_coordinates_geohash)(latitude, longitude)

    if _self.region == new_region:
        return

    await _self.remove_user_from_group(_self.region)
    await _self.channel_layer.group_discard(_self.region, _self.channel_name)

    await _self.add_user_to_group(new_region)
    await _self.channel_layer.group_add(new_region, _self.channel_name)
    _self.region = new_region
