from commons.exceptions.types import credits as credits_exceptions
from commons.validators import validate_iban_based_on_country
from django.db import transaction
from rest_framework import serializers

from credits.models import PayoutMethod
from credits.providers.stripe.utils import attach_payout_method


class ListPayoutMethodSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    country = serializers.CharField()
    currency = serializers.CharField()
    account_holder_name = serializers.CharField()
    account_number = serializers.CharField(source='masked_account_number')
    is_default = serializers.BooleanField()


class CreatePayoutMethodSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    is_default = serializers.BooleanField()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.has_accepted_account:
            raise credits_exceptions.EarningAccountIsNotAccepted()

        if not validate_iban_based_on_country(attrs['account_number'], user.earning_account.country):
            raise credits_exceptions.InvalidPayoutMethodForAccountCountry()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        is_default = validated_data['is_default']
        payout_method = PayoutMethod.objects.create(
            account=user.earning_account,
            currency=user.earning_account.currency,
            account_holder_name=user.earning_account.full_legal_name,
            account_number=validated_data['account_number'],
            country=user.earning_account.country,
            is_default=is_default,
        )

        if is_default:
            PayoutMethod.objects.filter(user=user).exclude(id=payout_method.id).update(is_default=False)

        payout = attach_payout_method(user.earning_account.payment_provider_id, payout_method, is_default=is_default)
        payout_method.payment_provider_id = payout.id
        payout_method.save()
        return payout_method
