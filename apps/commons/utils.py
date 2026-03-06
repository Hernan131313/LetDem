import hashlib
import random
import secrets

import geohash
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from dynamic_preferences.registries import global_preferences_registry

from commons.settings import PRECISION_NUMBER_TO_GEOHASH

global_preferences = global_preferences_registry.manager()


def generate_six_digits_otp():
    """Generate a 6-digit OTP"""
    return random.randint(100000, 999999)


def hash_otp(value: str):
    return hashlib.sha256(str(value).encode()).hexdigest()


def send_email(to_emails: list[str], subject: str, template: str = None, context: dict = None):
    # Render templates as string
    template_name = f'{template}.html'
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    # Create an email with both plain text and HTML
    email = EmailMultiAlternatives(subject, text_content, settings.FROM_EMAIL, to_emails)
    email.attach_alternative(html_content, 'text/html')

    # Send the email
    email.send()


def calculate_azimuth(previous_point: Point, current_point: Point):
    import math

    lon1, lat1 = math.radians(previous_point.x), math.radians(previous_point.y)
    lon2, lat2 = math.radians(current_point.x), math.radians(current_point.y)

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    azimuth = math.degrees(math.atan2(x, y))
    return (azimuth + 360) % 360


def generate_confirmation_code():
    return str(secrets.randbelow(10**6)).zfill(6)  # Ensures 6 digits, zero-padded


def generate_coordinates_geohash(lat: str, lng: str):
    precision = global_preferences[PRECISION_NUMBER_TO_GEOHASH]
    return geohash.encode(float(lat), float(lng), precision=precision)


def send_refresh_users_event(users: list):
    channel_layer = get_channel_layer()
    for user in users:
        group_name = f'users_{user.uuid.hex}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {'type': 'refresh_user', 'payload': {'reason': 'user.data.updated'}},
        )
