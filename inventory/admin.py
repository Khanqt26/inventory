from django.contrib import admin

from .models import Category, InventoryItem, MenuItem, Recipe, Sale, StockTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "quantity", "unit", "reorder_threshold", "is_low_stock"]
    list_filter = ["category"]
    search_fields = ["name"]


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ["item", "transaction_type", "quantity", "created_at", "note"]
    list_filter = ["transaction_type", "created_at"]
    search_fields = ["item__name", "note"]
    date_hierarchy = "created_at"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "is_available", "linked_item"]
    list_filter = ["category", "is_available"]
    search_fields = ["name", "description"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["menu_item", "item", "quantity_used"]
    list_filter = ["menu_item", "item"]
    search_fields = ["menu_item__name", "item__name"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ["menu_item", "quantity", "total_price", "created_at"]
    list_filter = ["created_at", "menu_item"]
    search_fields = ["menu_item__name"]
    date_hierarchy = "created_at"
