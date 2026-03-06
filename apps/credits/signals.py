import stripe
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from credits.models import PaymentMethod, PayoutMethod

stripe.api_key = settings.STRIPE_API_KEY


@receiver(post_delete, sender=PayoutMethod)
def delete_payout_method(sender, instance, **kwargs):
    if not instance.payment_provider_id:
        return
    try:
        stripe.Account.delete_external_account(instance.account.payment_provider_id, instance.payment_provider_id)
    except Exception:
        pass


@receiver(post_delete, sender=PaymentMethod)
def delete_payment_method(sender, instance, **kwargs):
    if not instance.payment_provider_id:
        return

    try:
        stripe.PaymentMethod.detach(instance.payment_provider_id)
    except Exception:
        pass
