from commons.utils import global_preferences
from django.conf import settings
from django.core.cache import cache
from geojson import Feature, Point
from mapbox import Directions, Geocoder

from maps import settings as maps_settings

# Initialize Mapbox Directions API
directions = Directions(access_token=settings.MAPBOX_ACCESS_TOKEN)
# Initialize the geocoder client
geocoder = Geocoder(access_token=settings.MAPBOX_ACCESS_TOKEN)


def get_coors_from_address(full_address):
    try:
        cache_key = f'mapbox:geocode:{full_address.replace(" ", "").lower()}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data['latitude'], cached_data['longitude']

        # Request geocoding
        response = geocoder.forward(full_address)
        response.raise_for_status()
        data_json = response.json()
        if not data_json['features']:
            return None

        feature = data_json['features'][0]
        longitude, latitude = feature['geometry']['coordinates']
        # Save result for 24 hours in cache
        cache.set(cache_key, {'latitude': latitude, 'longitude': longitude}, timeout=86400)
        return latitude, longitude
    except Exception:
        return None


def get_route_on_maps(origin, destination, is_full_address=True):
    # Convert coordinates into GeoJSON Features
    start_feature = Feature(geometry=Point((float(origin[1]), float(origin[0]))))
    if not is_full_address:
        end_feature = Feature(geometry=Point((float(destination[1]), float(destination[0]))))
    else:
        # Define destination address and get its coordinates
        latitude, longitude = get_coors_from_address(destination)
        end_feature = Feature(geometry=Point((float(longitude), float(latitude))))

    # Create a FeatureCollection
    route_features = [start_feature, end_feature]

    # Fetch route with real-time traffic data
    response = directions.directions(
        route_features,
        profile='mapbox/driving-traffic',  # Enable real-time traffic mode
        steps=True,
        annotations=['duration', 'speed'],
        geometries='geojson',
    )

    try:
        response.raise_for_status()
        data_json = response.json()
        if 'routes' not in data_json or not data_json['routes']:
            return None

        return data_json['routes'][0]
    except Exception:
        return None


def determine_congestion_level(route_data):
    """
    Estimate congestion level based on average speed.
    """
    if not route_data:
        return maps_settings.CONGESTION_LOW_LEVEL

    annotation = route_data['legs'][0]['annotation']
    speed = annotation['speed']  # Speed in meters per second

    if not speed:
        return maps_settings.CONGESTION_LOW_LEVEL

    avg_speed = sum(speed) / len(speed)  # Calculate average speed
    if avg_speed > global_preferences[maps_settings.SPEED_FOR_LOW_CONGESTION_DYNAMIC_PREFERENCE]:
        return maps_settings.CONGESTION_LOW_LEVEL
    elif avg_speed > global_preferences[maps_settings.SPEED_FOR_MODERATE_CONGESTION_DYNAMIC_PREFERENCE]:
        return maps_settings.CONGESTION_MODERATE_LEVEL

    return maps_settings.CONGESTION_HEAVY_LEVEL
