from django.urls import path

# Reuse existing views for v1 to align structure with other apps
from marketplace.v1.views import (
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
    path('categories/', CategoryListView.as_view(), name='v1.marketplace.category-list'),

    # Stores
    path('stores/', StoreListView.as_view(), name='v1.marketplace.store-list'),
    path('stores/<uuid:pk>/', StoreDetailView.as_view(), name='v1.marketplace.store-detail'),

    # Products
    path('products/', ProductListView.as_view(), name='v1.marketplace.product-list'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='v1.marketplace.product-detail'),

    # Vouchers
    path('vouchers/', VoucherListView.as_view(), name='v1.marketplace.voucher-list'),
    path('vouchers/<uuid:pk>/', VoucherDetailView.as_view(), name='v1.marketplace.voucher-detail'),
    path('vouchers/create-online/', CreateVoucherOnlineView.as_view(), name='v1.marketplace.create-voucher-online'),
    path('vouchers/validate/', ValidateVoucherView.as_view(), name='v1.marketplace.validate-voucher'),
    path('vouchers/pending/', PendingVouchersView.as_view(), name='v1.marketplace.pending-vouchers'),

    # Purchases and orders
    path('purchase/with-redeem/', PurchaseWithRedeemView.as_view(), name='v1.marketplace.purchase-with-redeem'),
    path('purchase/without-redeem/', PurchaseWithoutRedeemView.as_view(), name='v1.marketplace.purchase-without-redeem'),
    path('orders/', OrdersView.as_view(), name='v1.marketplace.orders'),

    # Admin (ad-hoc)
    path('admin/categories/', CategoryAdminCreateView.as_view(), name='v1.marketplace.admin-category-create'),
    path('admin/stores/', StoreAdminCreateView.as_view(), name='v1.marketplace.admin-store-create'),
    path('admin/products/', ProductAdminCreateView.as_view(), name='v1.marketplace.admin-product-create'),
    path('admin/panel/', MarketplaceAdminPanelView.as_view(), name='v1.marketplace.admin-panel'),
]
