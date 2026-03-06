import os

from .base import *  # noqa

DEBUG = True
LOCAL = True
ENVIRONMENT = 'local'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-m_+#_&cd&e56f!yhz0&t@w7!x_x8sa)2c400-ay%tpa7gafe16')

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}

# AWS ElasticCache configuration
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_CONNECTION_URI = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_CONNECTION_URI,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_CONNECTION_URI],
        },
    },
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery settings
CELERY_BROKER_URL = REDIS_CONNECTION_URI
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = f'{BASE_DIR}/staticfiles'

# Media files configuration for local development
MEDIA_URL = '/media/'
MEDIA_ROOT = f'{BASE_DIR}/media'

# CSRF Configuration for local development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.1.34:8000',
]

# Firebase config
FIREBASE_SERVICE_CONFIG = os.getenv('FIREBASE_SERVICE_CONFIG')

# MAILS Config
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
FROM_EMAIL = os.getenv('FROM_EMAIL')

VALIDATION_CODE_EXPIRE_TIME = os.getenv('VALIDATION_CODE_EXPIRE_TIME')  # In seconds

MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')

ONESIGNAL_APP_ID = os.getenv('ONESIGNAL_APP_ID')
ONESIGNAL_APP_KEY = os.getenv('ONESIGNAL_APP_KEY')
ONESIGNAL_USER_KEY = os.getenv('ONESIGNAL_USER_KEY')

STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
HTTP_STRIPE_SIGNATURE_ACCOUNTS = os.getenv('HTTP_STRIPE_SIGNATURE_ACCOUNTS')
HTTP_STRIPE_SIGNATURE_CONNECTED_ACCOUNTS = os.getenv('HTTP_STRIPE_SIGNATURE_CONNECTED_ACCOUNTS')
GDAL_LIBRARY_PATH = r"C:\GDAL\gdal.dll"
GEOS_LIBRARY_PATH = r"C:\GDAL\geos_c.dll"
