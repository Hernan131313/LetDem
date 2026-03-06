from commons.decorators import rate_limit
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.modules.auth.v1 import serializers as auth_serializers
from accounts.modules.users.v1 import serializers as users_serializers

User = get_user_model()


class LoginAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        user_data = users_serializers.UserSerializer(user).data
        return Response(
            {
                'token': user.auth_token.key,
                'is_active': user.is_active,
                'data': user_data,
            },
            status=status.HTTP_200_OK,
        )


class SignupAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Save the new user
        user_data = users_serializers.UserSerializer(user).data
        return Response(
            {
                'message': 'Account created successfully',
                'is_active': user.is_active,
                'token': user.auth_token.key,
                'data': user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class SocialLoginAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        user_data = users_serializers.UserSerializer(user).data
        return Response(
            data={
                'token': user.auth_token.key,
                'is_active': user.is_active,
                'data': user_data,
            },
            status=status.HTTP_200_OK,
        )


class SocialSignupAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.SocialSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Save the new user
        user_data = users_serializers.UserSerializer(user).data
        return Response(
            {
                'message': 'Account created successfully',
                'is_active': user.is_active,
                'token': user.auth_token.key,
                'data': user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class AccountVerificationAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.AccountVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response(
            {'token': user.auth_token.key, 'is_active': user.is_active},
            status=status.HTTP_200_OK,
        )


class AccountVerificationResendOTPAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    @rate_limit(limit=1, period=30, cache_key_prefix='account_verification')
    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.AccountVerificationResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={'message': 'Account verification OTP resent'}, status=status.HTTP_200_OK)


class PasswordResetAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={'message': 'Your password has been reset'}, status=status.HTTP_200_OK)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    @rate_limit(limit=1, period=30, cache_key_prefix='password_reset_request')
    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={'message': 'You have generated Reset Password OTP'}, status=status.HTTP_200_OK)


class PasswordResetValidateOTPAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.PasswordResetValidateOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={'is_validated': True}, status=status.HTTP_200_OK)


class PasswordResetResendOTPAPIView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users

    @rate_limit(limit=1, period=30, cache_key_prefix='password_reset')
    def post(self, request, *args, **kwargs):
        serializer = auth_serializers.PasswordResetResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={'message': 'The Reset Password OTP has been resend'}, status=status.HTTP_200_OK)
