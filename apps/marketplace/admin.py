from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Store, Product, Order, OrderItem, Voucher


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'icon', 'created')
    search_fields = ('name', 'display_name')
    list_filter = ('created',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rating', 'is_active', 'created')
    list_filter = ('category', 'is_active', 'created')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'discount', 'final_price', 'stock', 'rating', 'is_active')
    list_filter = ('store__category', 'is_active', 'created')
    search_fields = ('name', 'description', 'store__name')
    list_editable = ('is_active', 'stock')
    readonly_fields = ('final_price',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'subtotal', 'points_discount', 'total', 'used_points', 'created')
    list_filter = ('status', 'used_points', 'created')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('id', 'created', 'modified')
    inlines = [OrderItemInline]


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'user_email', 'product_name', 'store_name', 
        'status_badge', 'redeem_type', 'discount_percentage', 
        'expires_at', 'is_valid_badge', 'created'
    )
    list_filter = ('status', 'redeem_type', 'created', 'expires_at')
    search_fields = ('code', 'user__email', 'product__name', 'store__name')
    readonly_fields = (
        'id', 'code', 'user', 'product', 'store', 
        'points_used', 'created', 'modified', 'is_valid', 'is_expired'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'code', 'qr_code', 'scanned_code')
        }),
        ('Usuario y Producto', {
            'fields': ('user', 'product', 'store')
        }),
        ('Configuración', {
            'fields': ('redeem_type', 'status', 'discount_percentage', 'points_used')
        }),
        ('Fechas', {
            'fields': ('expires_at', 'redeemed_at', 'created', 'modified')
        }),
        ('Estado', {
            'fields': ('is_valid', 'is_expired')
        }),
    )
    
    @admin.display(description='Usuario', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.display(description='Producto', ordering='product__name')
    def product_name(self, obj):
        return obj.product.name
    @admin.display(description='Tienda', ordering='store__name')
    def store_name(self, obj):
        return obj.store.name
    @admin.display(description='Estado', ordering='status')
    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'REDEEMED': 'green',
            'EXPIRED': 'red',
            'CANCELLED': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    @admin.display(description='¿Válido?')
    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Válido</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Expirado</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">✗ No válido</span>'
            )
