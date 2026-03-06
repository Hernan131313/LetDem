from django.urls import path

from .views import (
    CategoryListView,
    StoreListView,
    StoreDetailView,
    ProductListView,
    ProductDetailView,
    VoucherListView,
    VoucherDetailView,
    PendingVouchersView,
    OrdersView,
    CreateVoucherOnlineView,
    ValidateVoucherView,
    PurchaseWithRedeemView,
    PurchaseWithoutRedeemView,
    CategoryAdminCreateView,
    StoreAdminCreateView,
    ProductAdminCreateView,
    MarketplaceAdminPanelView,
)


urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),

    # Stores
    path('stores/', StoreListView.as_view(), name='store-list'),
    path('stores/<uuid:pk>/', StoreDetailView.as_view(), name='store-detail'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # Vouchers
    path('vouchers/', VoucherListView.as_view(), name='voucher-list'),
    path('vouchers/<uuid:pk>/', VoucherDetailView.as_view(), name='voucher-detail'),
    path('vouchers/create-online/', CreateVoucherOnlineView.as_view(), name='create-voucher-online'),
    path('vouchers/validate/', ValidateVoucherView.as_view(), name='validate-voucher'),
    path('vouchers/pending/', PendingVouchersView.as_view(), name='pending-vouchers'),

    # Purchases and orders
    path('purchase/with-redeem/', PurchaseWithRedeemView.as_view(), name='purchase-with-redeem'),
    path('purchase/without-redeem/', PurchaseWithoutRedeemView.as_view(), name='purchase-without-redeem'),
    path('orders/', OrdersView.as_view(), name='orders'),

    # Admin (ad-hoc)
    path('admin/categories/', CategoryAdminCreateView.as_view(), name='admin-category-create'),
    path('admin/stores/', StoreAdminCreateView.as_view(), name='admin-store-create'),
    path('admin/products/', ProductAdminCreateView.as_view(), name='admin-product-create'),
    path('admin/panel/', MarketplaceAdminPanelView.as_view(), name='marketplace-admin-panel'),
]
