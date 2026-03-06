import time

import stripe
from commons.utils import global_preferences
from django.conf import settings

from credits import settings as credits_settings
from credits.models import AccountAddress, AccountIDDocument, EarningAccount, PayoutMethod
from credits.providers.stripe.decorators import handle_stripe_errors

stripe.api_key = settings.STRIPE_API_KEY


@handle_stripe_errors
def create_custom_account_connect(account_earning: EarningAccount):
    account_earning.refresh_from_db()
    return stripe.Account.create(
        type='custom',
        country=account_earning.country,
        email=account_earning.user.email,
        capabilities={'card_payments': {'requested': True}, 'transfers': {'requested': True}},
        business_type='individual',
        business_profile={'mcc': credits_settings.BUSINESS_PROFILE_MCC, 'url': credits_settings.BUSINESS_PROFILE_URL},
        settings={'payouts': {'schedule': {'interval': 'manual'}}},
        tos_acceptance={'date': int(time.time()), 'ip': account_earning.term_of_service['ip']},
        individual={
            'first_name': account_earning.legal_first_name,
            'last_name': account_earning.legal_last_name,
            'phone': account_earning.phone,
            'email': account_earning.user.email,
            'dob': {
                'day': account_earning.birthday.day,
                'month': account_earning.birthday.month,
                'year': account_earning.birthday.year,
            },
        },
        metadata={
            'user_id': account_earning.user.uuid.hex,
        },
    )


@handle_stripe_errors
def attach_address_to_custom_account_connect(account_id: str, account_address: AccountAddress):
    return stripe.Account.modify(
        account_id,
        individual={
            'address': {
                'line1': account_address.full_street,
                'city': account_address.city,
                'postal_code': account_address.postal_code,
                'country': account_address.country,
            },
        },
    )


@handle_stripe_errors
def attach_document_id_to_custom_account_connect(account_id: str, account_document: AccountIDDocument):
    return stripe.Account.modify(
        account_id,
        individual={
            'verification': {
                'document': {'front': account_document.front_side_token, 'back': account_document.back_side_token}
            },
        },
    )


@handle_stripe_errors
def attach_payout_method(account_id: str, payout_method: PayoutMethod, is_default=False):
    payout = stripe.Account.create_external_account(
        account_id,
        external_account={
            'object': 'bank_account',
            'account_holder_type': 'individual',
            'currency': payout_method.currency,
            'country': payout_method.country,
            'account_holder_name': payout_method.account_holder_name,
            'account_number': payout_method.account_number,
        },
    )

    if is_default:
        stripe.Account.modify_external_account(account_id, payout.id, default_for_currency=True)

    return payout


def process_payment_intent_response(payment_intent):
    if payment_intent.status in ['succeeded', 'requires_capture']:
        return {'status': 'success', 'message': 'Payment completed successfully.'}
    elif payment_intent.status == 'requires_action':
        return {
            'status': 'requires_action',
            'error_code': 'PAYMENT_REQUIRES_ACTION',
            'message': 'Authentication required.',
            'client_secret': payment_intent.client_secret,
        }
    else:
        return {
            'status': 'failed',
            'error_code': 'PAYMENT_FAILED',
            'message': (
                payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed.'
            ),
        }


@handle_stripe_errors
def create_payment_intent(reservation, payment_method):
    requester_customer_id = reservation.reserved_by.provider_customer_id
    space_owner_account_id = reservation.space.owner.earning_account.payment_provider_id
    space_owner_account_currency = reservation.space.owner.earning_account.currency
    payment_method_id = payment_method.payment_provider_id
    application_fees_percentage = global_preferences[credits_settings.APPLICATION_FEES_PERCENTAGE]
    application_fees_amount = int((application_fees_percentage / 100) * reservation.price)
    payment_intent_description = global_preferences[credits_settings.PAYMENT_INTENT_DESCRIPTION]

    return stripe.PaymentIntent.create(
        amount=reservation.price,
        currency=space_owner_account_currency,
        customer=requester_customer_id,
        payment_method=payment_method_id,
        confirm=True,
        capture_method='manual',
        application_fee_amount=application_fees_amount,
        transfer_data={'destination': space_owner_account_id},
        description=payment_intent_description,
        metadata={'reservation_id': str(reservation.uuid.hex)},
        automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
    )


@handle_stripe_errors
def mark_payment_method_as_default(customer_id, payment_method_id):
    return stripe.Customer.modify(customer_id, invoice_settings={'default_payment_method': payment_method_id})


@handle_stripe_errors
def attach_payment_method_to_customer(customer_id, payment_method_id, is_default=False):
    pm = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
    if is_default:
        mark_payment_method_as_default(customer_id, payment_method_id)

    return pm


@handle_stripe_errors
def capture_payment_intent(payment_intent_id):
    return stripe.PaymentIntent.capture(payment_intent_id)


@handle_stripe_errors
def cancel_payment_intent(payment_intent_id):
    return stripe.PaymentIntent.cancel(payment_intent_id)


@handle_stripe_errors
def retrieve_account_balance(account_id):
    return stripe.Balance.retrieve(stripe_account=account_id)


def get_account_available_balance(balance, currency):
    available_balances = balance.get('available', [])
    total_available_balance = sum(
        [
            available_balance['amount']
            for available_balance in available_balances
            if available_balance['currency'] == currency
        ]
    )
    return total_available_balance


def get_account_pending_balance(balance, currency):
    pending_balances = balance.get('pending', [])
    total_pending_balance = sum(
        [pending_balance['amount'] for pending_balance in pending_balances if pending_balance['currency'] == currency]
    )
    return total_pending_balance


@handle_stripe_errors
def create_payout_to_account(payout_method, account):
    return stripe.Payout.create(
        amount=account.available_balance,
        currency=account.currency,
        stripe_account=account.payment_provider_id,
        destination=payout_method.payment_provider_id,
        metadata={'account_id': account.payment_provider_id},
    )


@handle_stripe_errors
def create_marketplace_payment_intent(user, amount, currency='eur', payment_method_id=None):
    """
    Crea un PaymentIntent para compras de marketplace
    
    Args:
        user: Usuario que realiza la compra
        amount: Monto en centavos (ej: 1000 = 10.00 EUR)
        currency: Moneda (default: 'eur')
        payment_method_id: ID del método de pago (opcional)
    """
    customer_id = user.provider_customer_id
    
    payment_intent_params = {
        'amount': amount,
        'currency': currency,
        'customer': customer_id,
        'description': 'Compra en Marketplace LetDem',
        'metadata': {'user_id': str(user.id)},
    }
    
    if payment_method_id:
        payment_intent_params['payment_method'] = payment_method_id
        payment_intent_params['confirm'] = True
        payment_intent_params['automatic_payment_methods'] = {'enabled': True, 'allow_redirects': 'never'}
    else:
        payment_intent_params['automatic_payment_methods'] = {'enabled': True}
    
    return stripe.PaymentIntent.create(**payment_intent_params)
