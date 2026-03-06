from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    fields = ('type', 'road', 'direction', 'latitude', 'longitude')
    list_display = (
        'type',
        'road',
        'direction',
        'latitude',
        'longitude',
    )
    search_fields = ('road',)
