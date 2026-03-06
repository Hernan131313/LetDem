from django.contrib import admin
from django.utils import timezone

from .models import FreeSpace, PaidSpace, SpaceFeedback


# Custom filter for expiration
class ExpiredFilter(admin.SimpleListFilter):
    title = 'Expired'
    parameter_name = 'is_expired'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Expired'),
            ('no', 'Active'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'yes':
            return queryset.filter(expires_at__lt=now)
        if self.value() == 'no':
            return queryset.filter(expires_at__gte=now)
        return queryset


# -------- INLINE: Space Feedback --------
class SpaceFeedbackInline(admin.TabularInline):
    model = SpaceFeedback
    extra = 0
    readonly_fields = ('reported_by', 'type')
    can_delete = False
    verbose_name_plural = 'User Feedback'
    fk_name = 'space'  # Link to BaseSpace
    fields = (
        'type',
        'reported_by',
    )

    def reported_by_email(self, obj):
        return obj.reported_by.email if obj.reported_by else '-'

    reported_by_email.short_description = 'Reported By'

    def has_add_permission(self, request, obj=None):
        return False  # no adding

    def has_change_permission(self, request, obj=None):
        return False  # disables editing


# -------- BASE ADMIN --------
class BaseSpaceAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'type', 'street_name', 'owner_email', 'expires_at', 'is_expired')
    list_filter = ('type', ExpiredFilter)
    search_fields = ('street_name', 'id', 'uuid', 'owner__email')
    readonly_fields = (
        'geohash',
        'expires_at',
    )
    exclude = ('metadata', 'point')

    def owner_email(self, obj):
        return obj.owner.email if obj.owner else '-'

    owner_email.short_description = 'Owner Email'

    def is_expired(self, obj):
        return obj.is_expired

    is_expired.boolean = True


# -------- FREE SPACE ADMIN WITH INLINE FEEDBACK --------
@admin.register(FreeSpace)
class FreeSpaceAdmin(BaseSpaceAdmin):
    inlines = [SpaceFeedbackInline]


# -------- PAID SPACE ADMIN --------
@admin.register(PaidSpace)
class PaidSpaceAdmin(BaseSpaceAdmin):
    list_display = ('uuid', 'type', 'price_display', 'street_name', 'owner_email', 'phone', 'expires_at', 'is_expired')
    search_fields = ('street_name', 'phone', 'id', 'uuid', 'owner__email')

    def price_display(self, obj):
        return f'{obj.format_price:.2f}€'

    price_display.short_description = 'Price'
