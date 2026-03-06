from commons.exceptions.types.credits import PaymentMethodAlreadyExists
from django.db import transaction
from rest_framework import serializers

from credits.fields import YearMonthField
from credits.models import PaymentMethod
from credits.providers.stripe.utils import attach_payment_method_to_customer


class PaymentMethodSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='uuid', format='hex')
    holder_name = serializers.CharField()
    last4 = serializers.CharField()
    brand = serializers.CharField()
    expiration_date = YearMonthField()
    is_default = serializers.BooleanField()


class CreatePaymentMethodSerializer(serializers.Serializer):
    payment_method_id = serializers.CharField()
    holder_name = serializers.CharField()
    last4 = serializers.CharField()
    brand = serializers.CharField()
    expiration_date = YearMonthField()
    is_default = serializers.BooleanField()

    def validate(self, attrs):
        user = self.context['request'].user
        payment_method = PaymentMethod.objects.filter(user=user, payment_provider_id=attrs['payment_method_id']).last()
        if payment_method:
            raise PaymentMethodAlreadyExists()
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        customer_id = user.provider_customer_id
        payment_method_id = validated_data['payment_method_id']
        saves_as_default = validated_data['is_default']

        payment_method = PaymentMethod.objects.create(
            user=user,
            holder_name=validated_data['holder_name'],
            last4=validated_data['last4'],
            brand=validated_data['brand'],
            payment_provider_id=payment_method_id,
            expiration_date=validated_data['expiration_date'],
        )

        attach_payment_method_to_customer(customer_id, payment_method_id, saves_as_default)
        if saves_as_default:
            payment_method.mark_as_default()

        return payment_method
