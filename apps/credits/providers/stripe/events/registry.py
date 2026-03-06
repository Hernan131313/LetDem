from collections import defaultdict

from credits.providers.stripe.events import handlers

WEBHOOK_EVENTS_REGISTRY = defaultdict(
    lambda: lambda x: x,
    {
        'account.updated': handlers.account_updated_event_handler,
        'balance.available': handlers.balance_available_event_handler,
        'payment_intent.canceled': handlers.payment_intent_canceled_event_handler,
        'payment_intent.payment_failed': handlers.payment_intent_failed_event_handler,
        'payment_intent.amount_capturable_updated': handlers.payment_intent_amount_capturable_updated_event_handler,
        'charge.captured': handlers.payment_intent_charge_captured_event_handler,
        'payout.paid': handlers.payout_paid_event_handler,
        'payout.failed': handlers.payout_failed_event_handler,
        'payment_method.detached': handlers.payment_method_deleted_event_handler,
    },
)
