from commons.utils import global_preferences
from maps.settings import CONGESTION_HEAVY_LEVEL, CONGESTION_LOW_LEVEL, CONGESTION_MODERATE_LEVEL
from maps.utils import determine_congestion_level, get_route_on_maps

from spaces.settings import (
    DISTANCE_TO_GENERATE_CONGESTION_DYNAMIC_PREFERENCE,
    WEIGHT_FOR_HEAVY_CONGESTION_DYNAMIC_PREFERENCE,
    WEIGHT_FOR_LOW_CONGESTION_DYNAMIC_PREFERENCE,
    WEIGHT_FOR_MODERATE_CONGESTION_DYNAMIC_PREFERENCE,
)


def get_congestion_based_on_location(latitude, longitude):
    """
    Fetches real-time traffic speed & duration using Mapbox's Directions API.
    """
    # Define a nearby point to create a short route (~500m east)
    end_latitude = latitude
    end_longitude = longitude + global_preferences[DISTANCE_TO_GENERATE_CONGESTION_DYNAMIC_PREFERENCE]

    origin = (latitude, longitude)
    destination = (end_latitude, end_longitude)

    route_data = get_route_on_maps(origin, destination, is_full_address=False)
    if not route_data:
        return CONGESTION_LOW_LEVEL

    return determine_congestion_level(route_data)


def get_weight_based_on_congestion(congestion_level):
    """
    Returns points based on congestion level, if value not match return low value points
    """
    congestion_points_mapper = {
        CONGESTION_LOW_LEVEL: global_preferences[WEIGHT_FOR_LOW_CONGESTION_DYNAMIC_PREFERENCE],
        CONGESTION_MODERATE_LEVEL: global_preferences[WEIGHT_FOR_MODERATE_CONGESTION_DYNAMIC_PREFERENCE],
        CONGESTION_HEAVY_LEVEL: global_preferences[WEIGHT_FOR_HEAVY_CONGESTION_DYNAMIC_PREFERENCE],
    }
    return congestion_points_mapper.get(congestion_level, congestion_points_mapper[CONGESTION_LOW_LEVEL])
