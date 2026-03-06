from .base import *  # noqa

TEST = True
ENVIRONMENT = 'test'

SECRET_KEY = 'test_secret'

# Firebase config
FIREBASE_SERVICE_CONFIG = {}

# MAILS Config
EMAIL_HOST = 'test.host'
EMAIL_PORT = 0000
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
FROM_EMAIL = 'test@email.com'

VALIDATION_CODE_EXPIRE_TIME = 30  # In seconds

MAPBOX_ACCESS_TOKEN = 'token'

ONESIGNAL_APP_ID = 'onesignal_signal_id'
ONESIGNAL_APP_KEY = 'onesignal_app_key'
ONESIGNAL_USER_KEY = 'onesignal_user_key'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'TEST': {
            'NAME': 'test_db',
        },
    }
}
