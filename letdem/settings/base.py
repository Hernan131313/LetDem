import os
import sys
from pathlib import Path

from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add the 'apps' directory to the Python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
LOCAL = False
STAGING = False
TEST = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # 3rd Party Packages
    'channels',
    'dynamic_preferences',
    'dynamic_preferences.users.apps.UserPreferencesConfig',
    'storages',
    'django_redis',
    'django_celery_beat',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    # Django apps
    'accounts',
    'commons',
    'spaces',
    'events',
    'alerts',
    'maps',
    'credits',
    'reservations',
    'marketplace',
    # Should be in the bottom
    'django_cleanup.apps.CleanupConfig',
    'waffle',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

# Security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CORS_ALLOWED_ORIGINS = [
    'https://api-staging.letdem.org',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.1.103:8000',
]

# Permitir todas las origins en desarrollo (útil para móviles en la red local)
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'letdem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'letdem.wsgi.application'
ASGI_APPLICATION = 'letdem.asgi.application'


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

TIME_ZONE = 'UTC'

USE_I18N = True
LANGUAGE_CODE = 'en'  # default language

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'commons.exceptions.handlers.api_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

GEO_SRID = 4326

APPEND_SLASH = False

# Scheduled Celery Tasks
CELERY_BEAT_SCHEDULE = {
    'mark-expired-pending-reservation-to-status-expired-every-5-minutes': {
        'task': 'reservations.tasks.periodic.mark_expired_pending_reservations_to_status_expired_task',
        'schedule': crontab(minute='*/5'),
    },
    'cancel-not-confirmed-reservation-every-5-minutes': {
        'task': 'reservations.tasks.periodic.cancel_not_confirmed_reservation_periodic_task',
        'schedule': crontab(minute='*/5'),
    },
}

MARKETPLACE_STAGING_AUTH = {
    'ENABLED': False,
    'VERIFY_URL': os.getenv('MARKETPLACE_STAGING_VERIFY_URL', ''),
    'TIMEOUT': int(os.getenv('MARKETPLACE_STAGING_AUTH_TIMEOUT', 5)),
    'EMAIL_FIELD': os.getenv('MARKETPLACE_STAGING_AUTH_EMAIL_FIELD', 'email'),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
