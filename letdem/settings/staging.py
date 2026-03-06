from .base import *  # noqa
from commons.environment import get_aws_env


STAGING = True
ENVIRONMENT = 'staging'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_aws_env('SECRET_KEY')
DEBUG = get_aws_env('DEBUG')

# Configures s3 Storage
AWS_STORAGE_BUCKET_NAME = get_aws_env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
            'location': 'media',
            'querystring_auth': False,
            'file_overwrite': False,
            'default_acl': None,
            'object_parameters': {'CacheControl': 'max-age=86400'},
        },
    },
    'staticfiles': {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
            'location': 'static',
            'querystring_auth': False,
            'file_overwrite': False,
            'default_acl': None,
            'object_parameters': {'CacheControl': 'max-age=86400'},
        },
    },
}

# AWS RDS (Postgres) configuration
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_aws_env('DATABASE_NAME'),
        'USER': get_aws_env('DATABASE_USER'),
        'PASSWORD': get_aws_env('DATABASE_PASSWORD'),
        'HOST': get_aws_env('DATABASE_HOST'),
        'PORT': get_aws_env('DATABASE_PORT'),
    }
}

# AWS ElasticCache (Redis) configuration
REDIS_HOST = get_aws_env('REDIS_HOST')
REDIS_PORT = get_aws_env('REDIS_PORT', 6379)
REDIS_USERNAME = get_aws_env('REDIS_USERNAME')
REDIS_PASSWORD = get_aws_env('REDIS_PASSWORD')
REDIS_CONNECTION_URI = f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'

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

# Firebase config
FIREBASE_SERVICE_CONFIG = get_aws_env('FIREBASE_SERVICE_CONFIG')

# AWS SES Config
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = get_aws_env('AWS_SES_REGION_NAME')
AWS_SES_REGION_ENDPOINT = get_aws_env('AWS_SES_REGION_ENDPOINT')
FROM_EMAIL = get_aws_env('FROM_EMAIL')

VALIDATION_CODE_EXPIRE_TIME = get_aws_env('VALIDATION_CODE_EXPIRE_TIME')  # In seconds

# Mapbox API Key
MAPBOX_ACCESS_TOKEN = get_aws_env('MAPBOX_ACCESS_TOKEN')

# OneSignal
ONESIGNAL_APP_ID = get_aws_env('ONESIGNAL_APP_ID')
ONESIGNAL_APP_KEY = get_aws_env('ONESIGNAL_APP_KEY')
ONESIGNAL_USER_KEY = get_aws_env('ONESIGNAL_USER_KEY')

# Stripe
STRIPE_API_KEY = get_aws_env('STRIPE_API_KEY')
HTTP_STRIPE_SIGNATURE_ACCOUNTS = get_aws_env('HTTP_STRIPE_SIGNATURE_ACCOUNTS')
HTTP_STRIPE_SIGNATURE_CONNECTED_ACCOUNTS = get_aws_env('HTTP_STRIPE_SIGNATURE_CONNECTED_ACCOUNTS')
