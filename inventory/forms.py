from decimal import Decimal

from django import forms

from .models import Category, InventoryItem, InventorySettings


class InventoryItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            return
        settings_obj = InventorySettings.objects.order_by("id").first()
        if settings_obj:
            self.fields["reorder_threshold"].initial = settings_obj.default_reorder_threshold

    class Meta:
        model = InventoryItem
        fields = ["name", "category", "unit", "quantity", "reorder_threshold"]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name

    def clean_unit(self):
        unit = (self.cleaned_data.get("unit") or "").strip()
        if not unit:
            raise forms.ValidationError("Unit is required.")
        return unit

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None:
            return Decimal("0")
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_reorder_threshold(self):
        reorder_threshold = self.cleaned_data.get("reorder_threshold")
        if reorder_threshold is None:
            return Decimal("0")
        if reorder_threshold < 0:
            raise forms.ValidationError("Reorder threshold cannot be negative.")
        return reorder_threshold


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Category name is required.")
        return name


class InventorySettingsForm(forms.ModelForm):
    class Meta:
        model = InventorySettings
        fields = ["low_stock_alerts_enabled", "default_reorder_threshold"]

    def clean_default_reorder_threshold(self):
        threshold = self.cleaned_data.get("default_reorder_threshold")
        if threshold is None:
            return Decimal("0")
        if threshold < 0:
            raise forms.ValidationError("Default reorder threshold cannot be negative.")
        return threshold
