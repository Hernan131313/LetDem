from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import reservations.signals  # noqa
