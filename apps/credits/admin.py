from django.contrib import admin

from .models import (
    AccountAddress,
    AccountIDDocument,
    EarningAccount,
    PaymentMethod,
    PayoutMethod,
    Transaction,
    Withdraw,
)

# --------- INLINES (for EarningAccount) ---------


class AccountAddressInline(admin.TabularInline):
    model = AccountAddress
    extra = 0
    max_num = 1
    can_delete = False
    fields = ('id', 'full_street', 'city', 'postal_code', 'country')
    readonly_fields = ('full_street', 'city', 'postal_code', 'country')

    def has_add_permission(self, request, obj=None):
        return False  # no adding

    def has_change_permission(self, request, obj=None):
        return False  # disables editing


class AccountIDDocumentInline(admin.TabularInline):
    model = AccountIDDocument
    extra = 0
    max_num = 1
    can_delete = False
    fields = ('id', 'document_type', 'front_side_token', 'back_side_token')
    readonly_fields = ('document_type', 'front_side_token', 'back_side_token')

    def has_add_permission(self, request, obj=None):
        return False  # no adding

    def has_change_permission(self, request, obj=None):
        return False  # disables editing


class PayoutMethodInline(admin.TabularInline):
    model = PayoutMethod
    extra = 0
    can_delete = False
    fields = ('id', 'payment_provider_id', 'country', 'currency', 'account_holder_name', 'account_number', 'is_default')
    readonly_fields = (
        'payment_provider_id',
        'country',
        'currency',
        'account_holder_name',
        'account_number',
        'is_default',
    )

    def has_add_permission(self, request, obj=None):
        return False  # no adding

    def has_change_permission(self, request, obj=None):
        return False  # disables editing


# --------- MAIN ADMIN: EarningAccount ---------


@admin.register(EarningAccount)
class EarningAccountAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'payment_provider_id',
        'balance',
        'available_balance',
        'pending_balance',
        'status',
        'step',
        'country',
    )
    exclude = ('metadata',)  # hide metadata, keep provider ID read-only
    inlines = [
        AccountAddressInline,
        AccountIDDocumentInline,
        PayoutMethodInline,
    ]
    search_fields = ('user__email', 'legal_first_name', 'legal_last_name')
    list_filter = ('status', 'country')


# --------- SEPARATE ADMIN MODELS ---------


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_provider_id', 'holder_name', 'last4', 'brand', 'expiration_date', 'is_default')
    search_fields = ('user__email', 'holder_name', 'last4')  # search by user email
    exclude = ('metadata',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'payment_provider_id', 'account', 'format_amount', 'source')
    search_fields = ('account__user__email',)  # search by user email
    exclude = ('metadata',)


@admin.register(Withdraw)
class WithdrawAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'payment_provider_id', 'account', 'format_amount', 'status', 'masked_payout_method')
    search_fields = ('account__user__email',)  # search by user email
    list_filter = ('status',)  # filter by withdrawal status
    exclude = ('metadata',)
