from collections import defaultdict

BUSINESS_PROFILE_URL = 'https://letdem.com'
BUSINESS_PROFILE_MCC = '7523'

COUNTRIES_AVAILABLE_TO_CONNECT = 'credits__countries_available_to_connect'
MINIMUM_AGE_TO_CONNECT = 'credits__minimum_age_to_connect'
APPLICATION_FEES_PERCENTAGE = 'credits__payment_application_fees_percentage'
PAYMENT_INTENT_DESCRIPTION = 'credits__payment_intent_description'
MINIMUM_AMOUNT_TO_WITHDRAW = 'credits__minimum_amount_to_withdraw'


COUNTRY_CURRENCY = defaultdict(lambda: 'eur', {'ES': 'eur', 'GB': 'gbp'})
