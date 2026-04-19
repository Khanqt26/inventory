from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.CharField(max_length=20)
    quantity = models.FloatField(default=0)
    reorder_threshold = models.FloatField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_threshold


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} - {self.item.name} - {self.quantity} {self.item.unit}"


class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    linked_item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_used = models.FloatField()

    def __str__(self):
        return f"{self.menu_item.name} - {self.item.name} ({self.quantity_used})"


class Sale(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.menu_item.name} - {self.quantity} x ₱{self.total_price}"
