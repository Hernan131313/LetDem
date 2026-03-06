from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'space__owner',
        'reserved_by_user_email',
        'cancelled_by',
        'space',
        'status',
        'confirmation_code',
        'payment_provider_id',
        'cancelled_at',
    )
    search_fields = ('space__owner__email', 'reserved_by_user_email', 'confirmation_code', 'payment_provider_id')
    list_filter = ('status',)
    exclude = ('metadata',)  # hide metadata if exists
