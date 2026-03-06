import logging

import stripe
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response, status

from credits.providers.stripe.events import registry

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_API_KEY


class BaseStripeWebHookAPIView(APIView):
    """
    Base class to handle Stripe webhook events.
    Ensures signature validation, logging, and safe handler execution.
    """

    permission_classes = [AllowAny]
    endpoint_secret = None  # Must be set in subclasses

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.endpoint_secret)
        except stripe.error.SignatureVerificationError:
            logger.warning('⚠️ Invalid Stripe signature for event.')
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.error('❌ Invalid payload for Stripe event.')
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

        event_type = event['type']
        logger.info(f'📥 Stripe webhook received: {event_type}')

        event_handler = registry.WEBHOOK_EVENTS_REGISTRY[event_type]
        if event_handler is None:
            logger.warning(f'⚠️ No handler found for Stripe event: {event_type}')
            return Response({'message': f'No handler for event {event_type}'}, status=status.HTTP_200_OK)

        try:
            event_handler(event)
            logger.info(f'✅ Successfully handled Stripe event: {event_type}')
        except Exception as e:
            logger.exception(f'❌ Error processing Stripe event {event_type}: {str(e)}')
            return Response({'error': 'Failed to process event'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)


class StripeWebHookAccountsAPIView(BaseStripeWebHookAPIView):
    """Handles events for platform-level Stripe account."""

    endpoint_secret = settings.HTTP_STRIPE_SIGNATURE_ACCOUNTS


class StripeWebHookConnectedAccountAPIView(BaseStripeWebHookAPIView):
    """Handles events for connected accounts (Stripe Connect)."""

    endpoint_secret = settings.HTTP_STRIPE_SIGNATURE_CONNECTED_ACCOUNTS
