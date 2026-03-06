from django.apps import AppConfig
from accounts.backends.firebase import initialize_firebase


class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import accounts.signals  # noqa

        initialize_firebase()
