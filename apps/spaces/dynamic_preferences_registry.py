from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import FloatPreference, IntegerPreference

spaces = Section('spaces')


@global_preferences_registry.register
class MinimumTimeToPublishSpace(IntegerPreference):
    section = spaces
    name = 'minimum_time_to_publish_space'
    default = 15
    help_text = 'Minimum time in minutes to publish another event in same place'


@global_preferences_registry.register
class MinimumDistanceToPublishSpace(IntegerPreference):
    section = spaces
    name = 'minimum_distance_to_publish_space'
    default = 5
    help_text = 'Minimum distance in meters to publish another event'


@global_preferences_registry.register
class ExpirationTimeForSpaces(IntegerPreference):
    section = spaces
    name = 'expiration_time_for_spaces'
    default = 2
    help_text = 'Expiration time in hours to show spaces'


@global_preferences_registry.register
class WeightForLowCongestion(IntegerPreference):
    section = spaces
    name = 'weight_for_low_congestion'
    default = 2
    help_text = 'Weight to calculate points for low congestions'


@global_preferences_registry.register
class WeightForModerateCongestion(IntegerPreference):
    section = spaces
    name = 'weight_for_moderate_congestion'
    default = 4
    help_text = 'Weight to calculate points for moderate congestions'


@global_preferences_registry.register
class WeightForHeavyCongestion(IntegerPreference):
    section = spaces
    name = 'weight_for_heavy_congestion'
    default = 6
    help_text = 'Weight to calculate points for heavy congestions'


@global_preferences_registry.register
class DistanceToGenerateCongestion(FloatPreference):
    section = spaces
    name = 'distance_to_generate_congestion'
    default = 0.005
    help_text = 'Distance to generate end position from the original'


@global_preferences_registry.register
class MaxRadiusForScheduledNotifications(FloatPreference):
    section = spaces
    name = 'max_radius_for_scheduled_notifications'
    default = 1000
    help_text = 'Max Radius to look for scheduled notifications'


@global_preferences_registry.register
class PointsPerSpaceOccupied(IntegerPreference):
    section = spaces
    name = 'points_per_space_occupied'
    default = 3
    help_text = 'Number of points that the user earns when his space is occupied'


@global_preferences_registry.register
class MaxSpaceTimeToWait(IntegerPreference):
    section = spaces
    name = 'max_space_time_to_wait'
    default = 60
    help_text = 'Maximum time to wait in minutes'


@global_preferences_registry.register
class MinSpaceTimeToWait(IntegerPreference):
    section = spaces
    name = 'min_space_time_to_wait'
    default = 20
    help_text = 'Minimum time to wait in minutes'


@global_preferences_registry.register
class MinSpacePrice(IntegerPreference):
    section = spaces
    name = 'min_space_price'
    default = 3
    help_text = 'Minimum price for paid space'


@global_preferences_registry.register
class MaxSpacePrice(IntegerPreference):
    section = spaces
    name = 'max_space_price'
    default = 20
    help_text = 'Maximum price for paid space'


@global_preferences_registry.register
class MinutesToBlockSpace(IntegerPreference):
    section = spaces
    name = 'minutes_to_block_spaces'
    default = 5
    help_text = 'Minutes to block spaces'


@global_preferences_registry.register
class MinutesBeforeSpaceExpiration(IntegerPreference):
    section = spaces
    name = 'minutes_before_space_expiration'
    default = 2
    help_text = 'Minutes before space expiration'
