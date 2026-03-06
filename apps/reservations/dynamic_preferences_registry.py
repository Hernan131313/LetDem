from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference

spaces = Section('reservations')


@global_preferences_registry.register
class MinutesBeforeCancelReservation(IntegerPreference):
    section = spaces
    name = 'minutes_before_cancel_reservation'
    default = 15
    help_text = 'Minutes before cancel reservation'


@global_preferences_registry.register
class MinutesToCancelReservation(IntegerPreference):
    section = spaces
    name = 'minutes_to_cancel_reservation'
    default = 60
    help_text = 'Minutes to cancel reservation if not confirmed'
