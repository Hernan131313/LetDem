from commons.exceptions.types import credits as credits_exceptions
from commons.utils import global_preferences
from django.db import transaction
from rest_framework import serializers

from credits.models import EarningAccount, PayoutMethod, Transaction, Withdraw
from credits.providers.stripe.utils import create_payout_to_account
from credits.settings import MINIMUM_AMOUNT_TO_WITHDRAW


class ListWithdrawalSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    amount = serializers.DecimalField(max_digits=6, decimal_places=2, source='format_amount')
    status = serializers.CharField()
    masked_payout_method = serializers.CharField()
    created = serializers.DateTimeField()


class CreateWithdrawalSerializer(serializers.Serializer):
    payout_method_id = serializers.UUIDField()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.has_accepted_account:
            raise credits_exceptions.EarningAccountIsNotAccepted()

        minimum_amount = global_preferences[MINIMUM_AMOUNT_TO_WITHDRAW] * 100
        if user.earning_account.available_balance < minimum_amount:
            raise credits_exceptions.BalanceLowerThanTheMinimum()

        payout_method = PayoutMethod.objects.filter(account=user.earning_account, uuid=attrs['payout_method_id']).last()
        if not payout_method:
            raise credits_exceptions.PayoutMethodNotFound()

        attrs['payout_method'] = payout_method
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            user = self.context['request'].user
            payout_method = validated_data['payout_method']
            earning_account: EarningAccount = (
                EarningAccount.objects.select_for_update().filter(id=user.earning_account.id).last()
            )
            withdraw = Withdraw.objects.create(
                account=earning_account,
                amount=earning_account.available_balance,
                masked_payout_method=payout_method.masked_account_number,
            )
            withdraw_transaction = Transaction.objects.create(
                account=user.earning_account,
                amount=earning_account.available_balance,
                source=Transaction.Source.WITHDRAW,
            )

            earning_account.balance -= earning_account.available_balance
            earning_account.available_balance = 0
            earning_account.save()

            payout = create_payout_to_account(payout_method, user.earning_account)
            withdraw.payment_provider_id = payout.id
            withdraw.save()

            withdraw_transaction.payment_provider_id = payout.id
            withdraw_transaction.save()
            return withdraw
        except Exception:
            raise credits_exceptions.PayoutRequestFailed()
