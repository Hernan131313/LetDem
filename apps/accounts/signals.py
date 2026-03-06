import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

User = get_user_model()
stripe.api_key = settings.STRIPE_API_KEY


@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    """
    Create an auth token for the user once the user is created.
    """
    if not created:
        return

    # Create a token for the new user
    Token.objects.get_or_create(user=instance)

    # create customer on payment provider
    if instance.is_staff or instance.is_superuser:
        return

    customer = stripe.Customer.create(email=instance.email, metadata={'user_id': instance.uuid.hex})
    instance.provider_customer_id = customer.id
    instance.save()
