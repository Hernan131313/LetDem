from commons.exceptions.types import accounts as accounts_exceptions
from commons.utils import hash_otp
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.backends import firebase
from accounts.models import User, UserPreferences
from accounts.modules.auth.tasks import (
    create_user_device_task,
    reset_password_email_task,
    send_email_verification_task,
)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email'], social_id__isnull=True).last()

        if not user or not user.check_password(data['password']):
            raise accounts_exceptions.InvalidCredentials()

        if not user.is_active:
            raise accounts_exceptions.InactiveAccount()

        if device_id := data.get('device_id'):
            create_user_device_task.delay(user.id, device_id)

        user.last_login = timezone.now()
        user.save()
        return user


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_null=True)
    language = serializers.ChoiceField(choices=User.Languages.choices, required=False)

    def validate(self, data):
        # Check if this user already exists
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if user and user.is_active:
            raise accounts_exceptions.EmailAlreadyExists()

        # if the user already exists, but not active, we recreate the user account.
        if user and not user.is_active:
            user.delete()

        return data

    @transaction.atomic
    def create(self, validated_data):
        # Hash the password automatically and create the user
        password = validated_data.pop('password')
        device_id = validated_data.pop('device_id', None)
        validated_data['is_active'] = False
        user = User.objects.create_user(**validated_data)

        user.set_password(password)
        user.save()

        if device_id:
            create_user_device_task.delay(user.id, device_id)

        UserPreferences.objects.create(user=user)
        send_email_verification_task.delay(user.id)

        return user


class SocialLoginSerializer(serializers.Serializer):
    token = serializers.CharField()
    device_id = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        social_id = firebase.verify_firebase_token(data['token'])

        if not social_id:
            raise accounts_exceptions.InvalidSocialToken()

        user = User.objects.filter(social_id=social_id).last()
        if not user:
            raise accounts_exceptions.InvalidCredentials()

        user.last_login = timezone.now()

        if device_id := data.get('device_id'):
            create_user_device_task.delay(user.id, device_id)

        user.save()
        return user


class SocialSignupSerializer(serializers.Serializer):
    token = serializers.CharField()
    device_id = serializers.CharField(required=False, allow_null=True)
    language = serializers.ChoiceField(choices=User.Languages.choices, required=False)

    def validate(self, data: dict):
        # Get firebase user data
        firebase_user = firebase.get_firebase_user(data['token'])

        if not firebase_user:
            raise accounts_exceptions.InvalidSocialToken()

        if User.objects.filter(email=firebase_user.email).exists():
            raise accounts_exceptions.EmailAlreadyExists()

        # Get data fetched from firebase
        validated_data = {
            'social_id': firebase_user.uid,
            'email': firebase_user.email,
            'first_name': firebase_user.display_name or '',
            'device_id': data['device_id'],
            'language': data.get('language', 'en'),
        }

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        device_id = validated_data.pop('device_id')
        user = User.objects.create_user(**validated_data)
        UserPreferences.objects.create(user=user)

        if device_id:
            create_user_device_task.delay(user.id, device_id)

        return user


class AccountVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            raise accounts_exceptions.InvalidOTP()

        if user.is_active:
            raise accounts_exceptions.AccountAlreadyActivated()

        key = f'email_verification__{user.uuid.hex}'
        otp = cache.get(key)
        hashed_user_otp = hash_otp(data['otp'])

        if str(hashed_user_otp) != str(otp):
            raise accounts_exceptions.InvalidOTP()

        user.is_active = True
        user.save()

        cache.delete(key)
        return user


class AccountVerificationResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            return data

        send_email_verification_task.delay(user.id)
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            raise accounts_exceptions.EmailNotFound()

        if not hasattr(user, 'reset_password_requests'):
            raise accounts_exceptions.InvalidOTP()

        if not user.reset_password_requests.is_validated():
            raise accounts_exceptions.OTPNotValidated()

        user.set_password(data['password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            raise accounts_exceptions.EmailNotFound()

        if not user.is_active:
            raise accounts_exceptions.InactiveAccount()

        if user.is_social:
            raise accounts_exceptions.SocialUserCannotResetPassword()

        reset_password_email_task.delay(user.id)
        return user


class PasswordResetValidateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            raise accounts_exceptions.EmailNotFound()

        if not hasattr(user, 'reset_password_requests'):
            raise accounts_exceptions.InvalidOTP()

        password_request = user.reset_password_requests.ontime().first()
        if not password_request:
            raise accounts_exceptions.InvalidOTP()

        user_otp_hashed = hash_otp(data['otp'])
        if password_request.otp_hashed != user_otp_hashed:
            raise accounts_exceptions.InvalidOTP()

        user.reset_password_requests.validate()

        return user


class PasswordResetResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        data['email'] = data['email'].lower()
        user = User.objects.filter(email=data['email']).last()
        if not user:
            return data

        reset_password_email_task.delay(user.id)
        return data
