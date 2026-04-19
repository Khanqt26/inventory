from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from .models import Category, InventoryItem, MenuItem, Recipe, Sale, StockTransaction


@login_required
def menu_view(request):
    return redirect("dashboard")


@login_required
def order_item(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    recipes = Recipe.objects.filter(menu_item=menu_item).select_related("item")

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
            return redirect("menu_items")

    with transaction.atomic():
        for recipe in recipes:
            item = recipe.item
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
                return redirect("menu_items")

            StockTransaction.objects.create(
                item=item,
                transaction_type="out",
                quantity=amount_used,
                note=f"Used for {quantity} x {menu_item.name}",
            )

        Sale.objects.create(
            menu_item=menu_item,
            quantity=quantity,
            total_price=menu_item.price * quantity,
        )

    messages.success(request, f"{quantity} x {menu_item.name} ordered successfully.")
    return redirect("menu_items")


@login_required
def dashboard(request):
    total_sales = Sale.objects.aggregate(total=Sum("total_price"))["total"] or 0
    all_items = InventoryItem.objects.select_related("category").order_by("name")
    low_items = [item for item in all_items if item.is_low_stock]
    low_stock_percentage = min(100, len(low_items) * 20) if all_items else 0
    recent_transactions = StockTransaction.objects.select_related("item").order_by("-created_at")[:10]

    today = now().date()
    days = []
    sales_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        total = Sale.objects.filter(created_at__date=day).aggregate(total=Sum("total_price"))["total"] or 0
        days.append(day.strftime("%b %d"))
        sales_data.append(float(total))

    top_items = (
        Sale.objects.values("menu_item__name")
        .annotate(total_sold=Count("id"))
        .order_by("-total_sold")[:5]
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
            "days": days,
            "sales_data": sales_data,
            "top_items": top_items,
        },
    )


@login_required
def restock_all(request):
    with transaction.atomic():
        for item in InventoryItem.objects.all():
            added_quantity = max(0, 100 - item.quantity)
            InventoryItem.objects.filter(id=item.id).update(quantity=100, updated_at=now())

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
def restock_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    InventoryItem.objects.filter(id=item.id).update(quantity=F("quantity") + 20, updated_at=now())

    StockTransaction.objects.create(
        item=item,
        transaction_type="in",
        quantity=20,
        note="Individual restock",
    )

    messages.success(request, f"{item.name} was restocked by 20 {item.unit}.")
    return redirect("dashboard")


@login_required
def stock_in(request):
    if request.method == "POST":
        item = get_object_or_404(InventoryItem, id=request.POST.get("item"))
        quantity = float(request.POST.get("quantity", 0))
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Stock-in quantity must be greater than zero.")
            return redirect("stock_in")

        with transaction.atomic():
            InventoryItem.objects.filter(id=item.id).update(quantity=F("quantity") + quantity, updated_at=now())

            StockTransaction.objects.create(
                item=item,
                transaction_type="in",
                quantity=quantity,
                note=note,
            )

        messages.success(request, f"Added {quantity} {item.unit} of {item.name}.")
        return redirect("dashboard")

    items = InventoryItem.objects.select_related("category").order_by("name")
    return render(request, "inventory/stock_in.html", {"items": items})


@login_required
def stock_out(request):
    if request.method == "POST":
        item = get_object_or_404(InventoryItem, id=request.POST.get("item"))
        quantity = float(request.POST.get("quantity", 0))
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Stock-out quantity must be greater than zero.")
            return redirect("stock_out")

        with transaction.atomic():
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
        return redirect("dashboard")

    items = InventoryItem.objects.select_related("category").order_by("name")
    return render(request, "inventory/stock_out.html", {"items": items})


@login_required
def transaction_history(request, item_id=None):
    item = None

    if item_id:
        item = get_object_or_404(InventoryItem, id=item_id)
        transactions = StockTransaction.objects.filter(item=item).order_by("-date")
        title = f"Transaction History - {item.name}"
    else:
        transactions = StockTransaction.objects.select_related("item").order_by("-date")[:50]
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
    items = MenuItem.objects.filter(is_available=True).select_related("category").order_by("name")
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
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            Category.objects.create(name=name)
            messages.success(request, f'Category "{name}" created successfully.')
            return redirect("category_list")
        messages.error(request, "Category name is required.")

    return render(
        request,
        "inventory/category_form.html",
        {
            "title": "Create Category",
            "button_text": "Create Category",
        },
    )


@login_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            category.name = name
            category.save()
            messages.success(request, f'Category "{name}" updated successfully.')
            return redirect("category_list")
        messages.error(request, "Category name is required.")

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
    category_id = request.GET.get("category")
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
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        category_id = request.POST.get("category")
        unit = (request.POST.get("unit") or "").strip()
        quantity = request.POST.get("quantity", 0)
        reorder_threshold = request.POST.get("reorder_threshold", 10)

        try:
            if not name or not category_id or not unit:
                raise ValueError("Name, category, and unit are required.")

            category = Category.objects.get(id=category_id)
            item = InventoryItem.objects.create(
                name=name,
                category=category,
                unit=unit,
                quantity=float(quantity),
                reorder_threshold=float(reorder_threshold),
            )

            if float(quantity) > 0:
                StockTransaction.objects.create(
                    item=item,
                    transaction_type="in",
                    quantity=float(quantity),
                    note="Initial stock",
                )

            messages.success(request, f"Item '{item.name}' created successfully.")
            return redirect("inventory_detail", item_id=item.id)
        except Exception as error:
            messages.error(request, f"Error creating item: {error}")

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

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        category_id = request.POST.get("category")
        unit = (request.POST.get("unit") or "").strip()
        reorder_threshold = request.POST.get("reorder_threshold", 10)

        try:
            if not name or not category_id or not unit:
                raise ValueError("Name, category, and unit are required.")

            item.name = name
            item.category = Category.objects.get(id=category_id)
            item.unit = unit
            item.reorder_threshold = float(reorder_threshold)
            item.save()

            messages.success(request, f"Item '{item.name}' updated successfully.")
            return redirect("inventory_detail", item_id=item.id)
        except Exception as error:
            messages.error(request, f"Error updating item: {error}")

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
