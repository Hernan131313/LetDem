from django.apps import AppConfig


class SpacesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spaces'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import spaces.signals  # noqa
