from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import events.signals  # noqa
