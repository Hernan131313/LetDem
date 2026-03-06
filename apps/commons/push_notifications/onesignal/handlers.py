import functools

import onesignal
from django.conf import settings
from onesignal.api import default_api
from onesignal.models import Notification, StringMap

from commons.push_notifications.onesignal import settings as onesignal_settings


def get_notification_message(notification_type: str, params: dict):
    notification = onesignal_settings.NOTIFICATION_MESSAGE_SETTINGS[notification_type]
    return {
        'headings': {key: value.format(**(params or {})) for key, value in notification['headings'].items()},
        'contents': {key: value.format(**(params or {})) for key, value in notification['contents'].items()},
    }


def send_push_notification(device_id, notification_type, notification_data=None, params=None):
    """
    - device_id: represent the user device.
    - notification_type: which notification to send
    - notification_data: notification extra data
    - params: data to fulfill notification message
    - notification_message:
    {
        'headings': {'en': 'Message', 'es': 'Mensaje'},
        'contents': {'en': 'Message', 'es': 'Mensaje'},
    }
    """

    notification_message = get_notification_message(notification_type, params)

    def get_sections():
        return ['headings', 'contents']

    @functools.lru_cache
    def _client():
        # See configuration.py for a list of all supported configuration parameters.
        # Some of the OneSignal endpoints require USER_KEY bearer token for authorization as long as others require APP_KEY
        # (also knows as REST_API_KEY). We recommend adding both of them in the configuration page so that you will not need
        # to figure it yourself.
        configuration = onesignal.Configuration(
            app_key=settings.ONESIGNAL_APP_KEY, user_key=settings.ONESIGNAL_USER_KEY
        )
        api_client = onesignal.ApiClient(configuration)
        return default_api.DefaultApi(api_client)

    def create_notification(_sections):
        _notification = Notification()
        _notification.set_attribute('app_id', settings.ONESIGNAL_APP_ID)
        _notification.set_attribute('include_player_ids', [device_id])
        _notification.set_attribute('data', notification_data or {})

        for section in _sections:
            data_map = StringMap()
            for key, value in notification_message[section].items():
                data_map.set_attribute(key, value)
            _notification.set_attribute(section, data_map)

        return _notification

    api = _client()
    sections = get_sections()
    notification = create_notification(sections)
    return api.create_notification(notification)
