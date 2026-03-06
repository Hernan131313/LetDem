import tempfile
from datetime import date

import stripe
from commons.exceptions.base import EighteenYearsRequired, InvalidPhoneNumber
from commons.exceptions.types import credits as credits_exceptions
from commons.utils import global_preferences
from commons.validators import is_valid_phone_number, validate_iban_based_on_country
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from credits.models import AccountAddress, AccountIDDocument, EarningAccount, PayoutMethod
from credits.providers.stripe.utils import (
    attach_address_to_custom_account_connect,
    attach_document_id_to_custom_account_connect,
    attach_payout_method,
    create_custom_account_connect,
)
from credits.settings import (
    COUNTRIES_AVAILABLE_TO_CONNECT,
    COUNTRY_CURRENCY,
    MINIMUM_AGE_TO_CONNECT,
)
from credits.v1.serializers.payout_methods import ListPayoutMethodSerializer


class RetrieveAccountAddressSerializer(serializers.Serializer):
    full_street = serializers.CharField()
    city = serializers.CharField()
    postal_code = serializers.CharField()
    country = serializers.CharField()


class RetrieveAccountIDDocumentSerializer(serializers.Serializer):
    front_side_token = serializers.CharField()
    back_side_token = serializers.CharField()


class RetrieveEarningAccountSerializer(serializers.Serializer):
    balance = serializers.DecimalField(read_only=True, max_digits=6, decimal_places=2, source='format_balance')
    available_balance = serializers.DecimalField(
        read_only=True, max_digits=6, decimal_places=2, source='format_available_balance'
    )
    pending_balance = serializers.DecimalField(
        read_only=True, max_digits=6, decimal_places=2, source='format_pending_balance'
    )
    currency = serializers.SerializerMethodField()
    legal_first_name = serializers.CharField(read_only=True)
    legal_last_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    birthday = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    step = serializers.CharField(read_only=True)

    address = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    payout_methods = serializers.SerializerMethodField()

    def get_currency(self, instance: EarningAccount) -> str:
        return COUNTRY_CURRENCY[instance.country]

    def get_address(self, instance: EarningAccount) -> RetrieveAccountAddressSerializer | None:
        if not hasattr(instance, 'address') or not instance.address:
            return None
        return RetrieveAccountAddressSerializer(instance.address).data

    def get_document(self, instance: EarningAccount) -> RetrieveAccountIDDocumentSerializer | None:
        if not hasattr(instance, 'document') or not instance.document:
            return None
        return RetrieveAccountIDDocumentSerializer(instance.document).data

    def get_payout_methods(self, instance: EarningAccount) -> ListPayoutMethodSerializer | list:
        if not hasattr(instance, 'payout_methods'):
            return []
        payout_methods = instance.payout_methods.all()
        return ListPayoutMethodSerializer(payout_methods, many=True).data


class EarningAccountSerializer(serializers.Serializer):
    country = serializers.CharField()
    legal_first_name = serializers.CharField()
    legal_last_name = serializers.CharField()
    phone = serializers.CharField()
    birthday = serializers.DateField()
    user_ip = serializers.CharField()

    def _has_eighteen_or_more(self, birthday):
        today = date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        return age >= global_preferences[MINIMUM_AGE_TO_CONNECT]

    def validate(self, attrs):
        user = self.context['request'].user

        if user.has_earning_account:
            raise credits_exceptions.EarningAccountAlreadyExists()

        available_countries = global_preferences[COUNTRIES_AVAILABLE_TO_CONNECT].split(',')
        if attrs['country'] not in available_countries:
            raise credits_exceptions.CountryNotSupported()

        if not is_valid_phone_number(attrs['phone']):
            raise InvalidPhoneNumber()

        if not self._has_eighteen_or_more(attrs['birthday']):
            raise EighteenYearsRequired()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        earning_account = EarningAccount.objects.create(
            user=user,
            country=validated_data['country'],
            legal_first_name=validated_data['legal_first_name'],
            legal_last_name=validated_data['legal_last_name'],
            phone=validated_data['phone'],
            birthday=validated_data['birthday'],
            term_of_service={'ip': validated_data['user_ip']},
        )
        account = create_custom_account_connect(earning_account)
        earning_account.payment_provider_id = account.id
        earning_account.step = EarningAccount.Step.ADDRESS_INFO
        earning_account.save()
        return earning_account


class AccountAddressSerializer(serializers.Serializer):
    full_street = serializers.CharField()
    city = serializers.CharField()
    postal_code = serializers.CharField()
    country = serializers.CharField()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.has_earning_account:
            raise credits_exceptions.EarningAccountIsRequired()

        if user.earning_account.step != EarningAccount.Step.ADDRESS_INFO:
            raise credits_exceptions.BadRequestForCurrentStep()

        if attrs['country'] != user.earning_account.country:
            raise credits_exceptions.InvalidAddressCountry()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        account_address = AccountAddress.objects.create(
            account=user.earning_account,
            full_street=validated_data['full_street'],
            city=validated_data['city'],
            postal_code=validated_data['postal_code'],
            country=validated_data['country'],
        )
        custom_account_id = user.earning_account.payment_provider_id
        _ = attach_address_to_custom_account_connect(custom_account_id, account_address)
        user.earning_account.step = EarningAccount.Step.DOCUMENT_INFO
        user.earning_account.save()
        return account_address


class AccountIDDocumentSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=AccountIDDocument.Type.choices)
    front_side = Base64ImageField()
    back_side = Base64ImageField()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.has_earning_account:
            raise credits_exceptions.EarningAccountIsRequired()

        if user.earning_account.step != EarningAccount.Step.DOCUMENT_INFO:
            raise credits_exceptions.BadRequestForCurrentStep()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        document_type = validated_data['document_type']
        front_side = validated_data['front_side']
        back_side = validated_data['back_side']

        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_front_file:
            temp_front_file.write(front_side.read())  # ✅ write the file content
            temp_front_file.seek(0)
            file_front = stripe.File.create(purpose='identity_document', file=temp_front_file)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_back_file:
            temp_back_file.write(back_side.read())  # ✅ write the file content
            temp_back_file.seek(0)
            file_back = stripe.File.create(purpose='identity_document', file=temp_back_file)

        account_document = AccountIDDocument.objects.create(
            account=user.earning_account,
            document_type=document_type,
            front_side_token=file_front.id,
            back_side_token=file_back.id,
        )
        custom_account_id = user.earning_account.payment_provider_id
        _ = attach_document_id_to_custom_account_connect(custom_account_id, account_document)
        user.earning_account.step = EarningAccount.Step.BANK_ACCOUNT_INFO
        user.earning_account.save()
        return account_document


class CreatePayoutMethodSerializer(serializers.Serializer):
    account_number = serializers.CharField()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.has_earning_account:
            raise credits_exceptions.EarningAccountIsRequired()

        if user.earning_account.step != EarningAccount.Step.BANK_ACCOUNT_INFO:
            raise credits_exceptions.BadRequestForCurrentStep()

        if not validate_iban_based_on_country(attrs['account_number'], user.earning_account.country):
            raise credits_exceptions.InvalidPayoutMethodForAccountCountry()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        payout_method = PayoutMethod.objects.create(
            account=user.earning_account,
            currency=user.earning_account.currency,
            account_holder_name=user.earning_account.full_legal_name,
            account_number=validated_data['account_number'],
            country=user.earning_account.country,
            is_default=True,
        )
        earning_account = user.earning_account
        earning_account.status = EarningAccount.Status.PENDING
        earning_account.step = EarningAccount.Step.SUBMITTED
        earning_account.save()

        # Attach custom account
        custom_account_id = earning_account.payment_provider_id
        payout = attach_payout_method(custom_account_id, payout_method, is_default=True)
        payout_method.payment_provider_id = payout.id
        payout_method.save()

        return payout_method
