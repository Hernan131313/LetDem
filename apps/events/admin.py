from django.contrib import admin
from django.utils import timezone

from .models import Event, EventFeedback


# -------- INLINE: Event Feedback --------
class EventFeedbackInline(admin.TabularInline):
    model = EventFeedback
    extra = 0
    readonly_fields = ('reported_by', 'type')
    can_delete = False
    verbose_name_plural = 'User Feedback'
    fk_name = 'event'
    show_change_link = False

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


# -------- FILTER FOR EXPIRATION --------
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


# -------- MAIN ADMIN --------
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'street_name', 'owner_email', 'expires_at', 'is_expired', 'contribution_received')
    list_filter = ('type', ExpiredFilter)
    search_fields = ('street_name', 'id', 'owner__email')
    readonly_fields = ('point', 'geohash', 'expires_at', 'owner')
    exclude = ('metadata',)
    inlines = [EventFeedbackInline]

    def owner_email(self, obj):
        return obj.owner.email if obj.owner else '-'

    owner_email.short_description = 'Owner Email'

    def is_expired(self, obj):
        return obj.is_expired

    is_expired.boolean = True
