from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.functions import TruncDate
from django.db.models import Count, F, Sum
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate, now
from django.views.decorators.http import require_POST

from .forms import CategoryForm, InventoryItemForm, InventorySettingsForm
from .models import (
    Category,
    CustomerOrder,
    CustomerOrderLine,
    InventoryItem,
    InventorySettings,
    LowStockAlert,
    MenuItem,
    Recipe,
    Sale,
    StockTransaction,
)


def get_inventory_settings():
    settings_obj = InventorySettings.objects.order_by("id").first()
    if settings_obj:
        return settings_obj
    return InventorySettings.objects.create()


def add_low_stock_warning(request, item, action_label, previous_quantity=None):
    settings_obj = get_inventory_settings()
    if not settings_obj.low_stock_alerts_enabled:
        return
    item.refresh_from_db(fields=["quantity", "reorder_threshold"])
    active_alert_exists = LowStockAlert.objects.filter(item=item, resolved_at__isnull=True).exists()
    crossed_threshold = (
        previous_quantity is not None
        and previous_quantity > item.reorder_threshold
        and item.quantity <= item.reorder_threshold
    )

    if item.is_low_stock:
        if crossed_threshold or not active_alert_exists:
            LowStockAlert.objects.create(
                item=item,
                quantity_at_alert=item.quantity,
                threshold_at_alert=item.reorder_threshold,
                triggered_by=action_label,
            )
        messages.warning(
            request,
            f"Low stock alert: {item.name} is now at {item.quantity} {item.unit} after {action_label}. "
            f"Threshold: {item.reorder_threshold}.",
        )
        return

    LowStockAlert.objects.filter(item=item, resolved_at__isnull=True).update(resolved_at=now())


def _get_cart(request):
    return request.session.get("cashier_cart", {})


def _save_cart(request, cart):
    request.session["cashier_cart"] = cart
    request.session.modified = True


def _build_cart_context(cart):
    ids = [int(item_id) for item_id in cart.keys()]
    menu_items = {item.id: item for item in MenuItem.objects.filter(id__in=ids)}
    rows = []
    total = Decimal("0")
    for raw_id, qty in cart.items():
        item_id = int(raw_id)
        menu_item = menu_items.get(item_id)
        if not menu_item:
            continue
        quantity = max(1, int(qty))
        line_total = menu_item.price * quantity
        total += line_total
        rows.append(
            {
                "menu_item": menu_item,
                "quantity": quantity,
                "line_total": line_total,
            }
        )
    return rows, total


def _safe_cashier_redirect(request):
    next_url = (request.POST.get("next") or "").strip()
    if next_url.startswith("/cashier"):
        return redirect(next_url)
    return redirect("cashier_pos")


@login_required
def menu_view(request):
    return redirect("dashboard")


@login_required
@require_POST
def order_item(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    recipes = Recipe.objects.filter(menu_item=menu_item).select_related("item")

    next_url = request.POST.get("next")
    redirect_target = next_url if next_url and next_url.startswith("/") else "menu_items"

    try:
        quantity = max(1, int(request.POST.get("quantity", 1)))
    except (TypeError, ValueError):
        quantity = 1

    for recipe in recipes:
        required = recipe.quantity_used * quantity
        if recipe.item.quantity < required:
            messages.error(
                request,
                f"Not enough {recipe.item.name} for {quantity} x {menu_item.name}.",
            )
            return redirect(redirect_target)

    with transaction.atomic():
        for recipe in recipes:
            item = recipe.item
            previous_quantity = item.quantity
            amount_used = recipe.quantity_used * quantity
            updated = InventoryItem.objects.filter(
                id=item.id,
                quantity__gte=amount_used,
            ).update(quantity=F("quantity") - amount_used, updated_at=now())

            if not updated:
                messages.error(
                    request,
                    f"Not enough {item.name} for {quantity} x {menu_item.name}.",
                )
                return redirect(redirect_target)

            StockTransaction.objects.create(
                item=item,
                transaction_type="out",
                quantity=amount_used,
                note=f"Used for {quantity} x {menu_item.name}",
            )
            item.quantity = previous_quantity - amount_used
            item.updated_at = now()
            add_low_stock_warning(
                request,
                item,
                "order processing",
                previous_quantity=previous_quantity,
            )

        Sale.objects.create(
            menu_item=menu_item,
            quantity=quantity,
            total_price=menu_item.price * quantity,
        )

    messages.success(request, f"{quantity} x {menu_item.name} ordered successfully.")
    return redirect(redirect_target)


@login_required
def dashboard(request):
    alert_view = (request.GET.get("alert_view") or "active").strip().lower()
    if alert_view not in {"active", "snoozed", "acknowledged"}:
        alert_view = "active"

    total_sales = Sale.objects.aggregate(total=Sum("total_price"))["total"] or 0
    all_items = InventoryItem.objects.select_related("category").order_by("name")
    low_items = [item for item in all_items if item.is_low_stock]
    low_stock_percentage = min(100, len(low_items) * 20) if all_items else 0
    recent_transactions = StockTransaction.objects.select_related("item").order_by("-created_at")[:10]
    base_alert_qs = LowStockAlert.objects.select_related("item", "acknowledged_by", "snoozed_by").filter(
        resolved_at__isnull=True
    )
    if alert_view == "snoozed":
        recent_low_stock_alerts_qs = base_alert_qs.filter(snoozed_until__gt=now()).order_by("-snoozed_until")[:8]
    elif alert_view == "acknowledged":
        recent_low_stock_alerts_qs = base_alert_qs.filter(acknowledged_at__isnull=False).order_by("-acknowledged_at")[:8]
    else:
        recent_low_stock_alerts_qs = (
            base_alert_qs.filter(Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now()))
            .order_by("-created_at")[:8]
        )
    recent_low_stock_alerts = []
    for alert in recent_low_stock_alerts_qs:
        recommended = max(Decimal("0"), (alert.threshold_at_alert * Decimal("2")) - alert.item.quantity)
        recent_low_stock_alerts.append(
            {
                "alert": alert,
                "recommended_restock": recommended,
            }
        )
    acknowledged_alerts = (
        LowStockAlert.objects.select_related("item", "acknowledged_by")
        .filter(acknowledged_at__isnull=False)
        .order_by("-acknowledged_at")[:8]
    )

    return render(
        request,
        "inventory/dashboard.html",
        {
            "total_sales": total_sales,
            "low_items": low_items,
            "all_items": all_items,
            "low_stock_percentage": low_stock_percentage,
            "recent_transactions": recent_transactions,
            "recent_low_stock_alerts": recent_low_stock_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "alert_view": alert_view,
        },
    )


@login_required
def daily_sales(request):
    sales_qs = Sale.objects.select_related("menu_item").order_by("-created_at")
    today = localdate()

    daily_rows = (
        sales_qs.annotate(sale_date=TruncDate("created_at"))
        .values("sale_date")
        .annotate(
            total_sales=Sum("total_price"),
            total_items=Sum("quantity"),
            total_orders=Count("id"),
        )
        .order_by("-sale_date")
    )

    today_summary = next((row for row in daily_rows if row["sale_date"] == today), None)
    if not today_summary:
        today_summary = {
            "sale_date": today,
            "total_sales": Decimal("0"),
            "total_items": 0,
            "total_orders": 0,
        }

    recent_sales = sales_qs[:20]

    return render(
        request,
        "inventory/daily_sales.html",
        {
            "today_summary": today_summary,
            "daily_rows": daily_rows[:30],
            "recent_sales": recent_sales,
            "today": today,
        },
    )


@login_required
@require_POST
def restock_all(request):
    with transaction.atomic():
        for item in InventoryItem.objects.all():
            added_quantity = max(Decimal("0"), Decimal("100") - item.quantity)
            InventoryItem.objects.filter(id=item.id).update(quantity=Decimal("100"), updated_at=now())

            if added_quantity:
                StockTransaction.objects.create(
                    item=item,
                    transaction_type="in",
                    quantity=added_quantity,
                    note="Bulk restock",
                )

    messages.success(request, "All inventory items were restocked to 100.")
    return redirect("dashboard")


@login_required
@require_POST
def restock_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    previous_quantity = item.quantity
    InventoryItem.objects.filter(id=item.id).update(quantity=F("quantity") + Decimal("20"), updated_at=now())

    StockTransaction.objects.create(
        item=item,
        transaction_type="in",
        quantity=Decimal("20"),
        note="Individual restock",
    )

    messages.success(request, f"{item.name} was restocked by 20 {item.unit}.")
    add_low_stock_warning(request, item, "restocking", previous_quantity=previous_quantity)
    return redirect("dashboard")


@login_required
def stock_in(request):
    if request.method == "POST":
        item = get_object_or_404(InventoryItem, id=request.POST.get("item"))
        try:
            quantity = Decimal(str(request.POST.get("quantity", "0")))
        except (TypeError, ValueError, InvalidOperation):
            messages.error(request, "Stock-in quantity must be a valid number.")
            return redirect("stock_in")
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Stock-in quantity must be greater than zero.")
            return redirect("stock_in")

        with transaction.atomic():
            previous_quantity = item.quantity
            InventoryItem.objects.filter(id=item.id).update(quantity=F("quantity") + quantity, updated_at=now())

            StockTransaction.objects.create(
                item=item,
                transaction_type="in",
                quantity=quantity,
                note=note,
            )

        messages.success(request, f"Added {quantity} {item.unit} of {item.name}.")
        add_low_stock_warning(request, item, "stock in", previous_quantity=previous_quantity)
        return redirect("dashboard")

    items = InventoryItem.objects.select_related("category").order_by("name")
    return render(request, "inventory/stock_in.html", {"items": items})


@login_required
def stock_out(request):
    if request.method == "POST":
        item = get_object_or_404(InventoryItem, id=request.POST.get("item"))
        try:
            quantity = Decimal(str(request.POST.get("quantity", "0")))
        except (TypeError, ValueError, InvalidOperation):
            messages.error(request, "Stock-out quantity must be a valid number.")
            return redirect("stock_out")
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Stock-out quantity must be greater than zero.")
            return redirect("stock_out")

        with transaction.atomic():
            previous_quantity = item.quantity
            updated = InventoryItem.objects.filter(
                id=item.id,
                quantity__gte=quantity,
            ).update(quantity=F("quantity") - quantity, updated_at=now())

            if not updated:
                item.refresh_from_db(fields=["quantity"])
                messages.error(request, f"Insufficient stock. Only {item.quantity} {item.unit} available.")
                return redirect("stock_out")

            StockTransaction.objects.create(
                item=item,
                transaction_type="out",
                quantity=quantity,
                note=note,
            )

        messages.success(request, f"Removed {quantity} {item.unit} of {item.name}.")
        add_low_stock_warning(request, item, "stock out", previous_quantity=previous_quantity)
        return redirect("dashboard")

    items = InventoryItem.objects.select_related("category").order_by("name")
    return render(request, "inventory/stock_out.html", {"items": items})


@login_required
def stock_count_adjustment(request):
    items = list(InventoryItem.objects.select_related("category").order_by("name"))

    if request.method == "POST":
        updates = []
        errors = []
        note_suffix = (request.POST.get("adjustment_note") or "").strip()
        base_note = "Physical Count Adjustment"
        full_note = f"{base_note}: {note_suffix}" if note_suffix else base_note

        for item in items:
            raw_value = (request.POST.get(f"actual_{item.id}") or "").strip()
            if raw_value == "":
                continue
            try:
                actual_qty = Decimal(raw_value)
            except (TypeError, ValueError, InvalidOperation):
                errors.append(f"{item.name}: invalid number '{raw_value}'")
                continue
            if actual_qty < 0:
                errors.append(f"{item.name}: actual count cannot be negative")
                continue
            if actual_qty == item.quantity:
                continue
            updates.append((item, actual_qty))

        if errors:
            for err in errors[:10]:
                messages.error(request, err)
            if len(errors) > 10:
                messages.error(request, f"...and {len(errors) - 10} more errors.")
            return redirect("stock_count_adjustment")

        if not updates:
            messages.warning(request, "No count changes detected.")
            return redirect("stock_count_adjustment")

        with transaction.atomic():
            adjusted_in = Decimal("0")
            adjusted_out = Decimal("0")
            for item, actual_qty in updates:
                diff = actual_qty - item.quantity
                if diff > 0:
                    StockTransaction.objects.create(
                        item=item,
                        transaction_type="in",
                        quantity=diff,
                        note=full_note,
                    )
                    adjusted_in += diff
                else:
                    StockTransaction.objects.create(
                        item=item,
                        transaction_type="out",
                        quantity=abs(diff),
                        note=full_note,
                    )
                    adjusted_out += abs(diff)
                InventoryItem.objects.filter(id=item.id).update(quantity=actual_qty, updated_at=now())

        messages.success(
            request,
            f"Stock count applied to {len(updates)} items. Added: {adjusted_in}. Deducted: {adjusted_out}.",
        )
        return redirect("stock_count_adjustment")

    return render(request, "inventory/stock_count_adjustment.html", {"items": items})


@login_required
def transaction_history(request, item_id=None):
    item = None

    if item_id:
        item = get_object_or_404(InventoryItem, id=item_id)
        transactions = StockTransaction.objects.filter(item=item).order_by("-created_at")
        title = f"Transaction History - {item.name}"
    else:
        transactions = StockTransaction.objects.select_related("item").order_by("-created_at")[:50]
        title = "Recent Transactions"

    return render(
        request,
        "inventory/transaction_history.html",
        {
            "transactions": transactions,
            "title": title,
            "item": item,
        },
    )


def customer_menu(request):
    category_id = request.GET.get("category")
    categories = Category.objects.order_by("name")
    items = MenuItem.objects.select_related("category").order_by("name")
    selected_category = None

    if category_id:
        items = items.filter(category_id=category_id)
        selected_category = categories.filter(id=category_id).first()

    return render(
        request,
        "inventory/customer_menu.html",
        {
            "items": items,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


@login_required
def menu_items(request):
    category_id = request.GET.get("category")
    categories = Category.objects.order_by("name")
    items = MenuItem.objects.select_related("category").order_by("name")
    selected_category = None

    if category_id:
        items = items.filter(category_id=category_id)
        selected_category = categories.filter(id=category_id).first()

    return render(
        request,
        "inventory/menu_items.html",
        {
            "items": items,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


@login_required
def cashier_pos(request):
    category_id = request.GET.get("category")
    availability_filter = (request.GET.get("availability") or "available").strip().lower()
    if availability_filter not in {"available", "unavailable", "all"}:
        availability_filter = "available"
    status_filter = (request.GET.get("status") or "all").strip().lower()
    if status_filter not in {"all", "pending", "preparing", "served"}:
        status_filter = "all"
    categories = Category.objects.order_by("name")
    items = MenuItem.objects.select_related("category").order_by("name")
    if availability_filter == "available":
        items = items.filter(is_available=True)
    elif availability_filter == "unavailable":
        items = items.filter(is_available=False)
    selected_category = None
    if category_id:
        items = items.filter(category_id=category_id)
        selected_category = categories.filter(id=category_id).first()

    cart = _get_cart(request)
    cart_rows, cart_total = _build_cart_context(cart)
    recent_orders_qs = CustomerOrder.objects.select_related("created_by").order_by("-created_at")
    if status_filter != "all":
        recent_orders_qs = recent_orders_qs.filter(status=status_filter)
    recent_orders = recent_orders_qs[:12]
    return render(
        request,
        "inventory/cashier_pos.html",
        {
            "items": items,
            "categories": categories,
            "selected_category": selected_category,
            "cart_rows": cart_rows,
            "cart_total": cart_total,
            "recent_orders": recent_orders,
            "status_filter": status_filter,
            "availability_filter": availability_filter,
        },
    )


@login_required
@require_POST
def cashier_cart_add(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    cart = _get_cart(request)
    key = str(menu_item.id)
    cart[key] = int(cart.get(key, 0)) + 1
    _save_cart(request, cart)
    messages.success(request, f"Added {menu_item.name} to cart.")
    return _safe_cashier_redirect(request)


@login_required
@require_POST
def cashier_toggle_item_availability(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available"])
    state = "available" if item.is_available else "unavailable"
    messages.success(request, f"{item.name} marked as {state}.")
    return _safe_cashier_redirect(request)


@login_required
@require_POST
def cashier_cart_update(request, item_id):
    quantity_raw = request.POST.get("quantity", "1")
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        quantity = 1

    cart = _get_cart(request)
    key = str(item_id)
    if key in cart:
        if quantity <= 0:
            cart.pop(key, None)
        else:
            cart[key] = quantity
        _save_cart(request, cart)
    return _safe_cashier_redirect(request)


@login_required
@require_POST
def cashier_cart_remove(request, item_id):
    cart = _get_cart(request)
    cart.pop(str(item_id), None)
    _save_cart(request, cart)
    return _safe_cashier_redirect(request)


@login_required
@require_POST
def cashier_checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Cart is empty.")
        return _safe_cashier_redirect(request)

    payment_method = (request.POST.get("payment_method") or "cash").strip().lower()
    if payment_method not in {"cash", "card", "ewallet"}:
        payment_method = "cash"

    cart_rows, cart_total = _build_cart_context(cart)
    if not cart_rows:
        messages.error(request, "Cart items are unavailable.")
        _save_cart(request, {})
        return _safe_cashier_redirect(request)

    recipes = Recipe.objects.filter(menu_item__in=[r["menu_item"] for r in cart_rows]).select_related("item", "menu_item")
    recipe_map = {}
    for recipe in recipes:
        recipe_map.setdefault(recipe.menu_item_id, []).append(recipe)

    for row in cart_rows:
        for recipe in recipe_map.get(row["menu_item"].id, []):
            required = recipe.quantity_used * row["quantity"]
            if recipe.item.quantity < required:
                messages.error(
                    request,
                    f"Not enough {recipe.item.name} for {row['menu_item'].name}.",
                )
                return _safe_cashier_redirect(request)

    with transaction.atomic():
        order_number = f"ORD-{now().strftime('%Y%m%d%H%M%S%f')}"
        order = CustomerOrder.objects.create(
            order_number=order_number,
            status="pending",
            payment_method=payment_method,
            total_amount=cart_total,
            created_by=request.user,
        )
        for row in cart_rows:
            CustomerOrderLine.objects.create(
                order=order,
                menu_item=row["menu_item"],
                quantity=row["quantity"],
                unit_price=row["menu_item"].price,
                line_total=row["line_total"],
            )
            Sale.objects.create(
                menu_item=row["menu_item"],
                quantity=row["quantity"],
                total_price=row["line_total"],
            )
            for recipe in recipe_map.get(row["menu_item"].id, []):
                previous_quantity = recipe.item.quantity
                amount_used = recipe.quantity_used * row["quantity"]
                InventoryItem.objects.filter(id=recipe.item.id, quantity__gte=amount_used).update(
                    quantity=F("quantity") - amount_used,
                    updated_at=now(),
                )
                StockTransaction.objects.create(
                    item=recipe.item,
                    transaction_type="out",
                    quantity=amount_used,
                    note=f"Used for cashier checkout {order.order_number}",
                )
                recipe.item.quantity = previous_quantity - amount_used
                add_low_stock_warning(
                    request,
                    recipe.item,
                    f"cashier checkout {order.order_number}",
                    previous_quantity=previous_quantity,
                )

    _save_cart(request, {})
    messages.success(request, f"Checkout complete: {order.order_number}.")
    return _safe_cashier_redirect(request)


@login_required
@require_POST
def cashier_order_status_update(request, order_id):
    order = get_object_or_404(CustomerOrder, id=order_id)
    requested_status = (request.POST.get("status") or "").strip().lower()
    if requested_status not in {"pending", "preparing", "served"}:
        messages.error(request, "Invalid status update.")
        return redirect("cashier_pos")
    order.status = requested_status
    order.save(update_fields=["status"])
    messages.success(request, f"{order.order_number} marked as {order.get_status_display()}.")
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/cashier"):
        return redirect(next_url)
    return redirect("cashier_pos")


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@login_required
def category_list(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect("category_list")
        messages.error(request, form.errors.as_text())

    return render(
        request,
        "inventory/category_form.html",
        {
            "title": "Create Category",
            "button_text": "Create Category",
            "category": form.instance if form.instance.pk else None,
        },
    )


@login_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, instance=category)

    if request.method == "POST":
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect("category_list")
        messages.error(request, form.errors.as_text())

    return render(
        request,
        "inventory/category_form.html",
        {
            "title": "Update Category",
            "button_text": "Update Category",
            "category": category,
        },
    )


@login_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if MenuItem.objects.filter(category=category).exists() or InventoryItem.objects.filter(category=category).exists():
        messages.error(request, f'Cannot delete category "{category.name}" because it is still linked to items.')
        return redirect("category_list")

    if request.method == "POST":
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect("category_list")

    return render(request, "inventory/category_confirm_delete.html", {"category": category})


@login_required
def inventory_list(request):
    raw_category_id = (request.GET.get("category") or "").strip()
    category_id = raw_category_id if raw_category_id.isdigit() else ""
    search = (request.GET.get("search") or "").strip()

    queryset = InventoryItem.objects.select_related("category").order_by("name")

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if search:
        queryset = queryset.filter(name__icontains=search)

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "items": page_obj,
            "page_obj": page_obj,
            "categories": Category.objects.order_by("name"),
            "selected_category": category_id,
            "search_query": search,
            "low_stock_count": queryset.filter(quantity__lte=F("reorder_threshold")).count(),
        },
    )


@login_required
def inventory_detail(request, item_id):
    item = get_object_or_404(InventoryItem.objects.select_related("category"), id=item_id)
    transactions = StockTransaction.objects.filter(item=item).order_by("-created_at")[:10]

    return render(
        request,
        "inventory/inventory_detail.html",
        {
            "item": item,
            "transactions": transactions,
        },
    )


@login_required
def inventory_create(request):
    form = InventoryItemForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            if item.quantity > 0:
                StockTransaction.objects.create(
                    item=item,
                    transaction_type="in",
                    quantity=item.quantity,
                    note="Initial stock",
                )

            messages.success(request, f"Item '{item.name}' created successfully.")
            return redirect("inventory_detail", item_id=item.id)

        messages.error(request, form.errors.as_text())

    return render(
        request,
        "inventory/inventory_form.html",
        {
            "categories": Category.objects.order_by("name"),
            "action": "create",
        },
    )


@login_required
def inventory_update(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    previous_quantity = item.quantity
    form = InventoryItemForm(request.POST or None, instance=item)

    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Item '{item.name}' updated successfully.")
            add_low_stock_warning(request, item, "item update", previous_quantity=previous_quantity)
            return redirect("inventory_detail", item_id=item.id)

        messages.error(request, form.errors.as_text())

    return render(
        request,
        "inventory/inventory_form.html",
        {
            "item": item,
            "categories": Category.objects.order_by("name"),
            "action": "update",
        },
    )


@login_required
def inventory_delete(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == "POST":
        item_name = item.name
        item.delete()
        messages.success(request, f"Item '{item_name}' deleted successfully.")
        return redirect("inventory_list")

    return render(request, "inventory/inventory_confirm_delete.html", {"item": item})


@login_required
def inventory_settings(request):
    settings_obj = get_inventory_settings()
    form = InventorySettingsForm(request.POST or None, instance=settings_obj)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory settings updated successfully.")
            return redirect("inventory_settings")
        messages.error(request, form.errors.as_text())

    return render(
        request,
        "inventory/inventory_settings.html",
        {
            "settings_obj": settings_obj,
            "form": form,
        },
    )


@login_required
def menu_audit(request):
    required_categories = [
        "Burgers",
        "Bunwich & Hotdog",
        "Fries & Others",
        "Silog Meals",
        "Rice Meals",
        "Coolers",
        "Pizza",
        "Chicken & Pork Meals",
        "Chao Fan",
        "Mami",
        "Barkadahan",
        "Beef & Pork",
        "Seafood",
        "Chicken",
        "Noodles & Soup",
        "Rice & Vegies",
    ]

    duplicates = (
        MenuItem.objects.values("category__name", "name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .order_by("category__name", "name")
    )

    categories = Category.objects.order_by("name")
    category_counts = {row["category__name"]: row["count"] for row in MenuItem.objects.values("category__name").annotate(count=Count("id"))}
    missing_required = [name for name in required_categories if name not in {c.name for c in categories}]
    empty_categories = [c.name for c in categories if category_counts.get(c.name, 0) == 0]

    range_price_items = MenuItem.objects.filter(description__icontains="Price range").select_related("category").order_by("category__name", "name")
    unavailable_items = MenuItem.objects.filter(is_available=False).select_related("category").order_by("category__name", "name")

    return render(
        request,
        "inventory/menu_audit.html",
        {
            "duplicates": duplicates,
            "missing_required": missing_required,
            "empty_categories": empty_categories,
            "range_price_items": range_price_items,
            "unavailable_items": unavailable_items,
            "total_menu_items": MenuItem.objects.count(),
            "total_categories": categories.count(),
        },
    )


@login_required
@require_POST
def acknowledge_low_stock_alert(request, alert_id):
    alert = get_object_or_404(LowStockAlert, id=alert_id, resolved_at__isnull=True)
    alert.acknowledged_at = now()
    alert.acknowledged_by = request.user
    alert.save(update_fields=["acknowledged_at", "acknowledged_by"])
    messages.success(request, f"Alert acknowledged for {alert.item.name}.")
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/dashboard"):
        return redirect(next_url)
    return redirect("dashboard")


@login_required
@require_POST
def snooze_low_stock_alert(request, alert_id):
    alert = get_object_or_404(LowStockAlert, id=alert_id, resolved_at__isnull=True)
    alert.snoozed_until = now() + timedelta(hours=24)
    alert.snoozed_by = request.user
    alert.save(update_fields=["snoozed_until", "snoozed_by"])
    messages.success(request, f"Alert snoozed for 24 hours: {alert.item.name}.")
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/dashboard"):
        return redirect(next_url)
    return redirect("dashboard")
