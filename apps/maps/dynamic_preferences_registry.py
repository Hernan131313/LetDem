from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference

maps = Section('maps')


@global_preferences_registry.register
class SpeedForLowCongestionThreshold(IntegerPreference):
    section = maps
    name = 'speed_for_low_congestion_threshold'
    default = 15
    help_text = 'Speed to set a congestion as low - More than 15 m/s (~54 km/h)'


@global_preferences_registry.register
class SpeedForModerateCongestionThreshold(IntegerPreference):
    section = maps
    name = 'speed_for_moderate_congestion_threshold'
    default = 5
    help_text = 'Speed to set a congestion as moderate - Between 5-15 m/s (~18-54 km/h)'
