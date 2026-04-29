from django.db.models import F

from .models import InventoryItem


def inventory_alerts(request):
    if not request.user.is_authenticated:
        return {"global_low_stock_count": 0}
    count = InventoryItem.objects.filter(quantity__lte=F("reorder_threshold")).count()
    return {"global_low_stock_count": count}
