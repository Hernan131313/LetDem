from commons.models import AbstractUUIDModel
from django.contrib.gis.db import models

from credits.settings import COUNTRY_CURRENCY


class EarningAccount(AbstractUUIDModel):
    class Status(models.TextChoices):
        MISSING_INFO = 'MISSING_INFO', 'Missing info'
        PENDING = 'PENDING', 'Pending'
        REJECTED = 'REJECTED', 'Rejected'
        BLOCKED = 'BLOCKED', 'Blocked'
        ACCEPTED = 'ACCEPTED', 'Accepted'

    class Step(models.TextChoices):
        PERSONAL_INFO = 'PERSONAL_INFO', 'Personal info'
        ADDRESS_INFO = 'ADDRESS_INFO', 'Address info'
        DOCUMENT_INFO = 'DOCUMENT_INFO', 'Document info'
        BANK_ACCOUNT_INFO = 'BANK_ACCOUNT_INFO', 'Bank account info'
        SUBMITTED = 'SUBMITTED', 'Submitted'

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='earning_account')
    balance = models.IntegerField(default=0)
    available_balance = models.IntegerField(default=0)
    pending_balance = models.IntegerField(default=0)
    country = models.CharField(max_length=3)
    legal_first_name = models.CharField(max_length=200)
    legal_last_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    birthday = models.DateField()
    term_of_service = models.JSONField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.MISSING_INFO)
    step = models.CharField(max_length=20, choices=Step.choices, default=Step.PERSONAL_INFO)
    payment_provider_id = models.CharField(blank=True, null=True)

    @property
    def full_legal_name(self):
        return f'{self.legal_first_name} {self.legal_last_name}'

    @property
    def currency(self):
        return COUNTRY_CURRENCY[self.country]

    @property
    def is_accepted(self):
        return self.status == self.Status.ACCEPTED

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def is_blocked(self):
        return self.status == self.Status.BLOCKED

    @property
    def is_rejected(self):
        return self.status == self.Status.REJECTED

    @property
    def format_balance(self):
        return '{:.2f}'.format(self.balance / 100)

    @property
    def format_available_balance(self):
        return '{:.2f}'.format(self.available_balance / 100)

    @property
    def format_pending_balance(self):
        return '{:.2f}'.format(self.pending_balance / 100)

    @property
    def disabled_reason(self):
        self.metadata = self.metadata or {}
        return self.metadata.get('disabled_reason')

    def mark_as_accepted(self):
        self.status = self.Status.ACCEPTED
        self.step = self.Step.SUBMITTED
        self.metadata = self.metadata or {}
        self.metadata['disabled_reason'] = None
        self.save()

    def mark_as_pending(self):
        self.status = self.Status.PENDING
        self.metadata = self.metadata or {}
        self.metadata['disabled_reason'] = None
        self.save()

    def mark_as_rejected(self, disabled_reason):
        self.status = self.Status.REJECTED
        self.metadata = self.metadata or {}
        self.metadata['disabled_reason'] = disabled_reason
        self.save()

    def mark_as_blocked(self, disabled_reason):
        self.status = self.Status.BLOCKED
        self.metadata = self.metadata or {}
        self.metadata['disabled_reason'] = disabled_reason
        self.save()

    def __str__(self):
        return f'{self.user} ({self.status})'


class AccountAddress(AbstractUUIDModel):
    account = models.OneToOneField(EarningAccount, on_delete=models.CASCADE, related_name='address')
    full_street = models.CharField()
    city = models.CharField()
    postal_code = models.CharField()
    country = models.CharField()


class AccountIDDocument(AbstractUUIDModel):
    class Type(models.TextChoices):
        NATIONAL_ID = 'NATIONAL_ID', 'National ID'
        RESIDENT_PERMIT = 'RESIDENT_PERMIT', 'Resident Permit'

    account = models.OneToOneField(EarningAccount, on_delete=models.CASCADE, related_name='document')
    document_type = models.CharField(max_length=20, choices=Type.choices, default=Type.NATIONAL_ID)
    front_side_token = models.CharField()
    back_side_token = models.CharField()


class PayoutMethod(AbstractUUIDModel):
    account = models.ForeignKey(EarningAccount, on_delete=models.CASCADE, related_name='payout_methods')
    country = models.CharField()
    currency = models.CharField()
    account_holder_name = models.CharField()
    account_number = models.CharField()
    is_default = models.BooleanField(default=False)
    payment_provider_id = models.CharField(blank=True, null=True)

    def __str__(self):
        return self.masked_account_number

    @property
    def masked_account_number(self):
        return self.account_number[:4] + '*' * (len(self.account_number) - 8) + self.account_number[-4:]


class PaymentMethod(AbstractUUIDModel):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='payment_methods')
    payment_provider_id = models.CharField(null=True, blank=True)
    holder_name = models.CharField()
    last4 = models.CharField(max_length=4)
    brand = models.CharField()
    expiration_date = models.DateField(default=None, null=True)
    is_default = models.BooleanField(default=False)

    def mark_as_default(self):
        from credits.providers.stripe.utils import mark_payment_method_as_default

        mark_payment_method_as_default(self.user.provider_customer_id, self.payment_provider_id)
        self.__class__.objects.filter(user=self.user).update(is_default=False)
        self.is_default = True
        self.save()


class Transaction(AbstractUUIDModel):
    class Source(models.TextChoices):
        SPACE_PAYMENT = 'SPACE_PAYMENT', 'Space Payment'
        WITHDRAW = 'WITHDRAW', 'Withdraw'

    payment_provider_id = models.CharField(null=True, blank=True)
    account = models.ForeignKey(EarningAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    source = models.CharField(max_length=15, choices=Source.choices)

    @property
    def format_amount(self):
        return '{:.2f}'.format(self.amount / 100)

    @property
    def currency(self):
        return self.account.currency


class Withdraw(AbstractUUIDModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    account = models.ForeignKey(EarningAccount, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.IntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    masked_payout_method = models.CharField()
    payment_provider_id = models.CharField(null=True, blank=True)

    def __str__(self):
        return f'{self.status} - {self.format_amount} - {self.masked_payout_method}'

    @property
    def format_amount(self):
        return '{:.2f}'.format(self.amount / 100)

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.save()

    def mark_as_failed(self):
        self.status = self.Status.FAILED
        self.save()
