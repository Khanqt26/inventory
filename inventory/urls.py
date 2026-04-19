from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu_view, name='menu'),
    path('menu-items/', views.menu_items, name='menu_items'),
    path('order/<int:item_id>/', views.order_item, name='order'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('restock/', views.restock_all, name='restock'),
    path('restock-item/<int:item_id>/', views.restock_item, name='restock_item'),

    # Stock transaction URLs
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transactions/<int:item_id>/', views.transaction_history, name='item_transaction_history'),

    # Public menu
    path('customer/', views.customer_menu, name='customer_menu'),

    # Inventory management
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/create/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:item_id>/', views.inventory_detail, name='inventory_detail'),
    path('inventory/<int:item_id>/update/', views.inventory_update, name='inventory_update'),
    path('inventory/<int:item_id>/delete/', views.inventory_delete, name='inventory_delete'),

    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]
