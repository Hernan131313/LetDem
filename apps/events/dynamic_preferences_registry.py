from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference

events = Section('events')


@global_preferences_registry.register
class ExpirationTimeForEvents(IntegerPreference):
    section = events
    name = 'expiration_time_for_events'
    default = 1
    help_text = 'Expiration time in hours to show events'


@global_preferences_registry.register
class PointsPerEventCreation(IntegerPreference):
    section = events
    name = 'points_per_event_creation'
    default = 3
    help_text = 'Number of points that the user earns when publish an event'


@global_preferences_registry.register
class PointsPerEventFeedback(IntegerPreference):
    section = events
    name = 'points_per_event_feedback'
    default = 3
    help_text = 'Number of points that the user earns when sending event feedback'
