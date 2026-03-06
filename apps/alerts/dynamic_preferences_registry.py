from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference

events = Section('alerts')


@global_preferences_registry.register
class CacheExpirationTimeForAlerts(IntegerPreference):
    section = events
    name = 'cache_timeout_for_alerts'
    default = 30
    help_text = 'Cache Timeout For Alerts (in seconds)'
