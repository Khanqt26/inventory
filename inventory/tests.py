from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, InventoryItem, MenuItem, Recipe, Sale, StockTransaction


class InventoryFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="secure-password-123",
        )
        self.client.force_login(self.user)

        self.category = Category.objects.create(name="Coffee")
        self.item = InventoryItem.objects.create(
            name="Beans",
            category=self.category,
            unit="kg",
            quantity=Decimal("50"),
            reorder_threshold=Decimal("10"),
        )
        self.menu_item = MenuItem.objects.create(
            name="Americano",
            description="Test item",
            price=Decimal("120.00"),
            category=self.category,
            is_available=True,
        )
        Recipe.objects.create(menu_item=self.menu_item, item=self.item, quantity_used=Decimal("1.000"))

    def test_order_requires_post(self):
        response = self.client.get(reverse("order", args=[self.menu_item.id]))

        self.assertEqual(response.status_code, 405)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("50"))
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_order_decrements_stock_and_creates_sale(self):
        response = self.client.post(reverse("order", args=[self.menu_item.id]), {"quantity": "2"}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("48"))
        sale = Sale.objects.get()
        self.assertEqual(sale.quantity, 2)
        self.assertEqual(sale.total_price, Decimal("240.00"))
        self.assertEqual(StockTransaction.objects.filter(transaction_type="out").count(), 1)

    def test_order_respects_next_redirect(self):
        response = self.client.post(
            reverse("order", args=[self.menu_item.id]),
            {"quantity": "1", "next": reverse("dashboard")},
        )
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_order_with_insufficient_stock_does_not_mutate(self):
        self.item.quantity = Decimal("0.500")
        self.item.save(update_fields=["quantity"])

        response = self.client.post(reverse("order", args=[self.menu_item.id]), {"quantity": "1"}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("0.500"))
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_restock_all_requires_post(self):
        response = self.client.get(reverse("restock"))

        self.assertEqual(response.status_code, 405)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("50"))

    def test_restock_item_requires_post(self):
        response = self.client.get(reverse("restock_item", args=[self.item.id]))

        self.assertEqual(response.status_code, 405)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("50"))

    def test_stock_in_invalid_quantity_does_not_crash(self):
        response = self.client.post(
            reverse("stock_in"),
            {"item": self.item.id, "quantity": "not-a-number", "note": "bad payload"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("50"))
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_stock_out_invalid_quantity_does_not_crash(self):
        response = self.client.post(
            reverse("stock_out"),
            {"item": self.item.id, "quantity": "not-a-number", "note": "bad payload"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("50"))
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_inventory_create_rejects_negative_values(self):
        response = self.client.post(
            reverse("inventory_create"),
            {
                "name": "Milk",
                "category": self.category.id,
                "unit": "L",
                "quantity": "-1",
                "reorder_threshold": "-2",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(InventoryItem.objects.filter(name="Milk").exists())

    def test_inventory_list_ignores_invalid_category_param(self):
        InventoryItem.objects.create(
            name="Sugar",
            category=self.category,
            unit="kg",
            quantity=Decimal("5"),
            reorder_threshold=Decimal("1"),
        )
        response = self.client.get(reverse("inventory_list"), {"category": "None", "page": "2"})
        self.assertEqual(response.status_code, 200)


class CategorySlugTests(TestCase):
    def test_category_slug_is_made_unique(self):
        first = Category.objects.create(name="Special Drinks")
        second = Category.objects.create(name="Special Drinks")

        self.assertEqual(first.slug, "special-drinks")
        self.assertEqual(second.slug, "special-drinks-2")

    def test_category_slug_remains_unique_after_rename(self):
        first = Category.objects.create(name="Tea")
        second = Category.objects.create(name="Coffee")

        second.name = "Tea"
        second.slug = ""
        second.save()

        self.assertEqual(first.slug, "tea")
        self.assertEqual(second.slug, "tea-2")
