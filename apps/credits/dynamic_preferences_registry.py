from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntegerPreference, StringPreference

credits_section = Section('credits')


@global_preferences_registry.register
class CountriesAvailableToConnect(StringPreference):
    section = credits_section
    name = 'countries_available_to_connect'
    default = 'ES'
    help_text = 'Countries available to connect'


@global_preferences_registry.register
class MinimumAgeToConnect(IntegerPreference):
    section = credits_section
    name = 'minimum_age_to_connect'
    default = 18
    help_text = 'Minimum age to connect'


@global_preferences_registry.register
class PaymentApplicationFeesPercentage(IntegerPreference):
    section = credits_section
    name = 'payment_application_fees_percentage'
    default = 10
    help_text = 'Payment Application Fees Percentage'


@global_preferences_registry.register
class PaymentIntentDescription(StringPreference):
    section = credits_section
    name = 'payment_intent_description'
    default = 'LetDem - Parking Reservation'
    help_text = 'Payment Intent Description'


@global_preferences_registry.register
class MinimumAmountToWithdraw(IntegerPreference):
    section = credits_section
    name = 'minimum_amount_to_withdraw'
    default = 10
    help_text = 'Minimum amount to withdraw'
