from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference

commons = Section('commons')


@global_preferences_registry.register
class MetersToShowTooCloseModal(IntegerPreference):
    section = commons
    name = 'meters_to_show_too_close_modal'
    default = 10
    help_text = 'Meters to show to close modal'


@global_preferences_registry.register
class PrecisionNumberToGeoHash(IntegerPreference):
    section = commons
    name = 'precision_number_to_geohash'
    default = 5
    help_text = 'Precision number to generate geohash'
