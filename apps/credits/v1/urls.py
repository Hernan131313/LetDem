from django.urls import path, re_path

from credits.v1.views import (
    earnings,
    payment_methods,
    payout_methods,
    reservations,
    transactions,
    webhooks,
    withdrawals,
)

urlpatterns = [
    path('webhooks-accounts', webhooks.StripeWebHookAccountsAPIView.as_view(), name='webhooks-accounts'),
    path(
        'webhooks-connected-accounts',
        webhooks.StripeWebHookConnectedAccountAPIView.as_view(),
        name='webhooks-connected-accounts',
    ),
    path('earnings/account', earnings.EarningAccountAPIView.as_view(), name='earning-account'),
    path('earnings/address', earnings.AccountAddressAPIView.as_view(), name='earning-address'),
    path('earnings/document', earnings.AccountIDDocumentAPIView.as_view(), name='earning-document'),
    path('earnings/bank-account', earnings.AccountBankAccountAPIView.as_view(), name='earning-bank-account'),
    path('payment-methods', payment_methods.ListCreatePaymentMethodAPIView.as_view(), name='payment-methods'),
    path('payout-methods', payout_methods.ListCreatePayoutMethodAPIView.as_view(), name='payout-methods'),
    path('withdrawals', withdrawals.ListCreateWithdrawalAPIView.as_view(), name='withdrawals'),
    path('transactions', transactions.ListTransactionsAPIView.as_view(), name='transactions'),
    path('orders', reservations.ListOrdersAPIView.as_view(), name='orders'),
    path('reservations', reservations.ListReservationsAPIView.as_view(), name='reservations'),
    re_path(
        'payment-methods/(?P<uuid>[0-9a-fA-F]{32})/mark-as-default$',
        payment_methods.MarkAsDefaultPaymentMethodAPIView.as_view(),
        name='mark-payment-method-as-default',
    ),
    re_path(
        'payment-methods/(?P<uuid>[0-9a-fA-F]{32})$',
        payment_methods.DeletePaymentMethodAPIView.as_view(),
        name='delete-payment-method',
    ),
    re_path(
        'payout-methods/(?P<uuid>[0-9a-fA-F]{32})$',
        payout_methods.DeletePayoutMethodAPIView.as_view(),
        name='delete-payout-method',
    ),
]
