from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from accounts.models import Car, CarParkedPlace, Contribution, StaffUser, User, UserDevice

from .models import Notification


@admin.register(User)
class AccountUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_social')
    list_filter = ('is_active',)

    # Fields to use when viewing and editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when adding a new user via the admin
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                    'is_active',
                ),
            },
        ),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_staff=False, is_superuser=False)


@admin.register(StaffUser)
class StaffAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    # Fields to use when viewing and editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when adding a new user via the admin
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                    'is_staff',
                    'is_superuser',
                    'is_active',
                ),
            },
        ),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


class NotificationAdminForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['user', 'type', 'content_type', 'object_id', 'read']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the content_type queryset to only those where model is 'freespace' and 'paidspace'
        self.fields['content_type'].queryset = ContentType.objects.filter(model__in=['freespace', 'paidspace'])


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm
    list_display = ('id', 'user', 'type', 'read', 'get_content_object', 'created')
    list_filter = ('type', 'read')
    search_fields = ('user__email',)

    def get_content_object(self, obj):
        return obj.content_object

    get_content_object.short_description = 'Content Object'


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device_id', 'created')
    search_fields = ('user__username',)


class CarParkedPlaceInline(admin.TabularInline):  # or TabularInline if you prefer a table layout
    model = CarParkedPlace
    fields = ('street_name', 'latitude', 'longitude')
    list_display = ('id', 'street_name', 'latitude', 'longitude')
    can_delete = False  # usually you don't want to delete parked place directly
    extra = 0
    verbose_name_plural = 'Last Parked Place'
    fk_name = 'car'  # specify the OneToOne relation

    def has_add_permission(self, request, obj=None):
        return False  # no adding

    def has_change_permission(self, request, obj=None):
        return False  # disables editing


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    fields = ('user', 'name', 'plate_number', 'label')
    list_display = ('id', 'user', 'name', 'plate_number', 'label')
    list_filter = ('label',)
    search_fields = ('name', 'plate_number')
    ordering = ('name',)
    readonly_fields = ('id',)
    inlines = [CarParkedPlaceInline]


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    fields = ('user', 'type', 'action', 'points', 'created')
    list_display = ('id', 'user', 'type', 'action', 'points', 'created')
    list_filter = ('type', 'action')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created', 'modified')
