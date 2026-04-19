from django.contrib import admin
from .models import Category, InventoryItem, StockTransaction, MenuItem, Recipe, Sale

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'quantity', 'unit', 'reorder_threshold', 'is_low_stock']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'date', 'note']
    list_filter = ['transaction_type', 'date']
    search_fields = ['item__name', 'note']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'linked_item']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']

admin.site.register(Recipe)
admin.site.register(Sale)