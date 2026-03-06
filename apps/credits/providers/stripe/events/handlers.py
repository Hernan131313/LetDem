from commons.utils import send_refresh_users_event
from django.db import transaction
from maps.signals import refresh_maps
from reservations.models import Reservation
from reservations.signals import space_has_been_reserved

from credits.models import EarningAccount, PaymentMethod, Transaction, Withdraw
from credits.providers.stripe.utils import (
    get_account_available_balance,
    get_account_pending_balance,
    retrieve_account_balance,
)


def account_updated_event_handler(event):
    from credits.tasks import send_notification_earning_account_accepted_task

    account = event['data']['object']
    # Access important fields
    charges_enabled = account.get('charges_enabled')
    payouts_enabled = account.get('payouts_enabled')

    # Check requirements to see some disabled reason
    requirements = account.get('requirements', {})
    disabled_reason = requirements.get('disabled_reason')

    earning_account: EarningAccount = EarningAccount.objects.filter(payment_provider_id=account['id']).last()
    if not earning_account:
        return

    if charges_enabled and payouts_enabled:
        if earning_account.is_accepted:
            return
        earning_account.mark_as_accepted()
        send_notification_earning_account_accepted_task.delay(earning_account.user.id)
    elif earning_account.is_pending and disabled_reason is not None:
        earning_account.mark_as_rejected(disabled_reason)
    elif earning_account.is_accepted and disabled_reason is not None:
        earning_account.mark_as_blocked(disabled_reason)
    elif disabled_reason is None:
        earning_account.mark_as_pending()

    send_refresh_users_event(users=[earning_account.user])


@transaction.atomic
def balance_available_event_handler(event):
    balance = event['data']['object']
    connected_account_id = event.get('account')

    if not connected_account_id:
        return

    earning_account: EarningAccount = (
        EarningAccount.objects.select_for_update().filter(payment_provider_id=connected_account_id).last()
    )
    if not earning_account:
        return

    available_balance = get_account_available_balance(balance, earning_account.currency)
    pending_balance = get_account_pending_balance(balance, earning_account.currency)
    earning_account.available_balance = available_balance
    earning_account.pending_balance = pending_balance
    earning_account.balance = available_balance + pending_balance
    earning_account.save()

    send_refresh_users_event(users=[earning_account.user])


@transaction.atomic
def payment_intent_amount_capturable_updated_event_handler(event):
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']

    reservation = Reservation.objects.filter(payment_provider_id=payment_intent_id).last()
    if not reservation:
        return

    is_space_reserved = Reservation.objects.reserved().filter(space=reservation.space).last()
    if reservation.status != Reservation.Status.PENDING:
        return

    if is_space_reserved or reservation.space.is_expired:
        reservation.metadata = {'cancellation_reason': 'space_reserved' if is_space_reserved else 'space_expired'}
        reservation.save()
        reservation.cancel()
        return

    reservation.status = Reservation.Status.RESERVED
    reservation.save()

    space_has_been_reserved.send(sender=None, instance=reservation)
    refresh_maps.send(None, instance=reservation.space)


@transaction.atomic
def payment_intent_charge_captured_event_handler(event):
    charge = event['data']['object']
    payment_intent_id = charge['payment_intent']

    reservation = Reservation.objects.reserved().filter(payment_provider_id=payment_intent_id).last()
    if not reservation:
        return

    reservation.status = Reservation.Status.CONFIRMED
    reservation.save()

    if not reservation.space.owner:
        return

    earning_account = EarningAccount.objects.select_for_update().filter(user=reservation.space.owner).last()
    if not earning_account:
        return

    balance = retrieve_account_balance(earning_account.payment_provider_id).to_dict()
    available_balance = get_account_available_balance(balance, earning_account.currency)
    pending_balance = get_account_pending_balance(balance, earning_account.currency)
    earning_account.available_balance = available_balance
    earning_account.pending_balance = pending_balance
    earning_account.balance = available_balance + pending_balance
    earning_account.save()

    amount_captured = charge['amount_captured']
    application_fee_amount = charge['application_fee_amount'] or 0.0
    earned_amount = amount_captured - application_fee_amount
    Transaction.objects.create(account=earning_account, amount=earned_amount, source=Transaction.Source.SPACE_PAYMENT)

    # TODO: Send space owner a notification with new balance earned
    send_refresh_users_event(users=[earning_account.user])


@transaction.atomic
def payment_intent_canceled_event_handler(event):
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']

    reservation = Reservation.objects.filter(payment_provider_id=payment_intent_id).last()
    if not reservation or reservation.status == reservation.Status.CANCELLED:
        return

    reservation.status = Reservation.Status.CANCELLED
    reservation.metadata = {'cancellation_reason': 'cancelled'}
    reservation.save()


@transaction.atomic
def payment_intent_failed_event_handler(event):
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']

    reservation = Reservation.objects.filter(payment_provider_id=payment_intent_id).last()
    if not reservation or reservation.status == reservation.Status.CANCELLED:
        return

    reservation.unlock()


@transaction.atomic
def payout_paid_event_handler(event):
    payout = event['data']['object']
    withdraw = Withdraw.objects.filter(payment_provider_id=payout['id']).last()
    if not withdraw:
        return

    withdraw.mark_as_completed()
    earning_account = EarningAccount.objects.select_for_update().filter(id=withdraw.account.id).last()
    if not earning_account:
        return

    balance = retrieve_account_balance(earning_account.payment_provider_id).to_dict()
    available_balance = get_account_available_balance(balance, earning_account.currency)
    pending_balance = get_account_pending_balance(balance, earning_account.currency)
    earning_account.available_balance = available_balance
    earning_account.pending_balance = pending_balance
    earning_account.balance = available_balance + pending_balance
    earning_account.save()


@transaction.atomic
def payout_failed_event_handler(event):
    payout = event['data']['object']
    withdraw = Withdraw.objects.filter(payment_provider_id=payout['id']).last()
    if not withdraw:
        return

    withdraw.mark_as_failed()
    earning_account = EarningAccount.objects.select_for_update().filter(id=withdraw.account.id).last()
    if not earning_account:
        return

    Transaction.objects.filter(payment_provider_id=payout['id']).delete()
    balance = retrieve_account_balance(earning_account.payment_provider_id).to_dict()
    available_balance = get_account_available_balance(balance, earning_account.currency)
    pending_balance = get_account_pending_balance(balance, earning_account.currency)
    earning_account.available_balance = available_balance
    earning_account.pending_balance = pending_balance
    earning_account.balance = available_balance + pending_balance
    earning_account.save()


@transaction.atomic
def payment_method_deleted_event_handler(event):
    payment_method_id = event['data']['object']['id']
    payment_method = PaymentMethod.objects.filter(payment_provider_id=payment_method_id).last()
    if not payment_method:
        return

    payment_method.delete()
