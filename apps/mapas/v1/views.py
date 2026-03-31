from datetime import timedelta

from commons.validators import is_valid_coordinates
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from maps.utils import determine_congestion_level, get_route_on_maps
from maps.v1 import serializers


class MapsNearbyAPIView(APIView):
    """
    API View to list spaces, events, and alerts, filtered by query parameters:
    - `?options=spaces,events,alerts` → Includes spaces, events and alerts nearby in response
    - `?current-point=2.89489,-3.0787` → Current user location
    - `?previous-point=2.89489,-3.0787` → Last user location (if first time same as user-current)
    - `?driving-mode=true` → Determines if user is requesting in driving mode
    - `?radius=50` → Determines the meters to take into account
    """

    permission_classes = [IsAuthenticated]

    SERIALIZER_OPTIONS = {
        'spaces': serializers.serializer_spaces,
        'events': serializers.serializer_events,
        'alerts': serializers.serializer_alerts,
    }

    def get(self, request, *args, **kwargs):
        serializer = {}
        options = request.query_params.get('options')
        is_driving_mode = request.query_params.get('driving-mode') in ['true', 'True']

        current_point = request.query_params.get('current-point')
        previous_point = request.query_params.get('previous-point')
        radius = request.query_params.get('radius', '200')

        if not current_point:
            return Response(
                {'message': '`current-point` is required as query params'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_point = current_point.split(',')
        if not is_valid_coordinates(current_point[0], current_point[1]):
            return Response(
                {'message': '`current-point` is not a valid point'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not options:
            return Response(
                {'message': '`options` is required as query params. Choices: `spaces`, `events`, `alerts`'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = options.rstrip(',').split(',')
        if len(options) > 3:  # To avoid bad requests sending a lot of options
            return Response(
                {'message': 'Too many options received. Choices: `spaces`, `events`, `alerts`'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_driving_mode and not previous_point:
            return Response(
                {'message': '`previous-point` is required as query params when `driving-mode=true`'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_driving_mode:
            previous_point = previous_point.split(',')
            if not is_valid_coordinates(previous_point[0], previous_point[1]):
                return Response(
                    {'message': '`previous-point` is not a valid point'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not radius.isdigit():
            return Response(
                {'message': '`radius` should be a valid digit'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for option in options:
            option = option.strip()
            if option not in self.SERIALIZER_OPTIONS:
                continue

            serializer[option] = self.SERIALIZER_OPTIONS[option](
                request, current_point, radius, previous_point=previous_point, user=request.user
            )

        return Response(serializer, status=status.HTTP_200_OK)


class MapsRoutesAPIView(APIView):
    """
    API View to get routes based:
    - `?current-point=2.89489,-3.0787` → Current user location
    - `?destination-address=calle de leganes, 4` → Destination full address
    - `?destination-point=2.89489,-3.0787` → User destionation
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        current_point = request.query_params.get('current-point')
        destination_address = request.query_params.get('destination-address')
        destination_point = request.query_params.get('destination-point')

        if not current_point:
            return Response(
                {'message': '`current-point` is required as query params'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_point = current_point.split(',')
        if not is_valid_coordinates(current_point[0], current_point[1]):
            return Response(
                {'message': '`current-point` is not a valid point'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        route = None
        if destination_address:
            route = get_route_on_maps(current_point, destination_address)
        else:
            if not destination_point:
                return Response(
                    {'message': '`destination-point` is required when destination_address is not provided'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            destination_point = destination_point.split(',')
            if not is_valid_coordinates(destination_point[0], destination_point[1]):
                return Response(
                    {'message': '`destination-point` is not a valid point'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            route = get_route_on_maps(current_point, destination_point, is_full_address=False)

        duration = round(route['duration'] / 60)
        distance = round(route['distance'])
        polylines = route['geometry']['coordinates']
        arriving_at = timezone.now() + timedelta(minutes=duration)
        routes_list = [
            {
                'polylines': polylines,
                'distance': distance,  # In meters
                'duration': duration,  # In minutes
                'traffic_level': determine_congestion_level(route),  # low, moderate, heavy
                'arriving_at': arriving_at,
            }
        ]

        return Response(data={'routes': routes_list}, status=status.HTTP_200_OK)
