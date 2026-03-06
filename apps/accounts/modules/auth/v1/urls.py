from django.urls import path

from accounts.modules.auth.v1 import views

urlpatterns = [
    path('login', views.LoginAPIView.as_view(), name='v1.login'),
    path('signup', views.SignupAPIView.as_view(), name='v1.signup'),
    path('social-login', views.SocialLoginAPIView.as_view(), name='v1.social-login'),
    path('social-signup', views.SocialSignupAPIView.as_view(), name='v1.social-signup'),
    path(
        'account-verification/validate',
        views.AccountVerificationAPIView.as_view(),
        name='v1.account-verification-validate',
    ),
    path(
        'account-verification/resend-otp',
        views.AccountVerificationResendOTPAPIView.as_view(),
        name='v1.account-verification-resend-otp',
    ),
    path(
        'password-reset/request',
        views.PasswordResetRequestAPIView.as_view(),
        name='v1.password-reset-request',
    ),
    path(
        'password-reset/validate',
        views.PasswordResetValidateOTPAPIView.as_view(),
        name='v1.password-reset-validate',
    ),
    path(
        'password-reset/resend-otp',
        views.PasswordResetResendOTPAPIView.as_view(),
        name='v1.password-reset-resend-otp',
    ),
    path('password-reset', views.PasswordResetAPIView.as_view(), name='v1.password-reset'),
]
