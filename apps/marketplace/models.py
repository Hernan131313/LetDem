from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from commons.models import AbstractUUIDModel


class Category(AbstractUUIDModel):
    """Marketplace store categories."""

    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text=_('Emoji or icon reference'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']

    def __str__(self) -> str:
        return self.display_name


class Store(AbstractUUIDModel):
    """Marketplace stores."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stores')
    image_url = models.URLField(blank=True)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0.0,
        help_text=_('Store latitude in decimal degrees'),
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0.0,
        help_text=_('Store longitude in decimal degrees'),
    )
    address = models.CharField(max_length=300, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    is_open = models.BooleanField(
        default=True,
        help_text=_('Indicates whether the store is currently open'),
    )
    opening_hours = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Opening hours, e.g. '09:00 - 21:00'"),
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Total number of reviews'),
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Store')
        verbose_name_plural = _('Stores')
        ordering = ['-created']

    def __str__(self) -> str:
        return self.name


class Product(AbstractUUIDModel):
    """Marketplace products."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created']

    @property
    def final_price(self) -> float:
        """Return the final price after applying the discount percentage."""
        return float(self.price) * (1 - float(self.discount) / 100)

    def __str__(self) -> str:
        return f'{self.name} - {self.store.name}'


class Order(AbstractUUIDModel):
    """Purchase orders."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PAID = 'PAID', _('Paid')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='marketplace_orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    points_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    used_points = models.BooleanField(default=False)
    points_used_amount = models.PositiveIntegerField(
        default=0,
        help_text=_('Amount of loyalty points spent on the order'),
    )

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self) -> str:
        return f'Order {self.id} - {self.user.email} - {self.status}'


class OrderItem(AbstractUUIDModel):
    """Order items."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('Order item')
        verbose_name_plural = _('Order items')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.product.name} x{self.quantity}'


class Voucher(AbstractUUIDModel):
    """Vouchers generated from point redemptions."""

    class RedeemType(models.TextChoices):
        IN_STORE = 'IN_STORE', _('In store')
        ONLINE = 'ONLINE', _('Online')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        REDEEMED = 'REDEEMED', _('Redeemed')
        EXPIRED = 'EXPIRED', _('Expired')
        CANCELLED = 'CANCELLED', _('Cancelled')

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='vouchers',
        help_text=_('User that generated the voucher'),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='vouchers',
        help_text=_('Product the voucher belongs to'),
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='vouchers',
        help_text=_('Store that owns the product'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique voucher code (e.g. LETDEM-12345)'),
    )
    qr_code = models.TextField(
        blank=True,
        help_text=_('QR code representation (base64 or URL)'),
    )
    redeem_type = models.CharField(
        max_length=20,
        choices=RedeemType.choices,
        help_text=_('Redemption type (in store or online)'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current voucher status'),
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Discount percentage (e.g. 30 for 30%)'),
    )
    points_used = models.PositiveIntegerField(
        default=500,
        help_text=_('Number of points spent to generate the voucher'),
    )
    expires_at = models.DateTimeField(
        help_text=_('Expiration date and time (48 hours after creation by default)'),
    )
    redeemed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Date and time when the voucher was redeemed'),
    )
    scanned_code = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Legacy field used to store scanned product codes'),
    )

    class Meta:
        verbose_name = _('Voucher')
        verbose_name_plural = _('Vouchers')
        ordering = ['-created']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.code} - {self.user.email} - {self.status}'

    @property
    def is_valid(self) -> bool:
        """Return True if the voucher can still be redeemed."""
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()

    @property
    def is_expired(self) -> bool:
        """Return True if the voucher is expired."""
        return self.expires_at <= timezone.now()
