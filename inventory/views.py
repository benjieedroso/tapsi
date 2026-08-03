from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import IngredientForm, IngredientTransactionForm
from .models import Ingredient, InventoryTransaction, LowStockAlert


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


# ── Ingredient Views (FR-040, FR-041) ────────────────────────────────


@login_required
def ingredient_list(request):
    """Read access for all staff (SRS role matrix: Inventory = R for
    Cashier/Kitchen)."""
    rid = _restaurant_id(request.user)
    q = request.GET.get("q", "").strip()
    low_stock = request.GET.get("low_stock") == "1"

    ingredients = Ingredient.objects.filter(restaurant_id=rid, is_deleted=False)
    if q:
        ingredients = ingredients.filter(name__icontains=q)

    # FR-041: stock is derived from the ledger — annotate with the latest
    # resulting balance instead of storing a stock figure.
    latest_balance = (
        InventoryTransaction.objects.filter(ingredient_id=OuterRef("pk"))
        .order_by("-id")
        .values("resulting_balance")[:1]
    )
    ingredients = ingredients.annotate(stock=Subquery(latest_balance)).order_by("name")

    low_stock_list = None
    if low_stock:
        low_stock_list = [
            i for i in ingredients if (i.stock or 0) <= i.minimum_stock
        ]

    open_alerts = LowStockAlert.objects.filter(
        restaurant_id=rid,
        resolved_at__isnull=True,
    ).select_related("ingredient")

    return render(request, "inventory/ingredient_list.html", {
        "ingredients": ingredients,
        "open_alerts": open_alerts,
        "q": q,
        "low_stock_filter": low_stock,
        "low_stock_list": low_stock_list,
    })


@user_passes_test(_is_manager_or_above)
def ingredient_create(request):
    rid = _restaurant_id(request.user)
    form = IngredientForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        ingredient = form.save(commit=False)
        ingredient.restaurant_id = rid
        ingredient.save()
        messages.success(request, f"Ingredient \"{ingredient.name}\" created.")
        return redirect("inventory:ingredient_list")
    return render(request, "inventory/ingredient_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def ingredient_edit(request, pk):
    rid = _restaurant_id(request.user)
    ingredient = get_object_or_404(Ingredient, pk=pk, restaurant_id=rid, is_deleted=False)
    form = IngredientForm(request.POST or None, instance=ingredient, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Ingredient \"{ingredient.name}\" updated.")
        return redirect("inventory:ingredient_list")
    return render(request, "inventory/ingredient_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def ingredient_delete(request, pk):
    """Soft delete — the ledger and stock cards stay intact (FR-043)."""
    rid = _restaurant_id(request.user)
    ingredient = get_object_or_404(Ingredient, pk=pk, restaurant_id=rid, is_deleted=False)
    ingredient.soft_delete()
    messages.success(request, f"Ingredient \"{ingredient.name}\" deleted.")
    return redirect("inventory:ingredient_list")


# ── Stock Card (FR-046) ──────────────────────────────────────────────


@login_required
def stock_card(request, pk):
    """FR-046: per-ingredient ledger with running balance, filterable by
    date range and type."""
    rid = _restaurant_id(request.user)
    ingredient = get_object_or_404(Ingredient, pk=pk, restaurant_id=rid)

    transactions = InventoryTransaction.objects.filter(
        restaurant_id=rid,
        ingredient=ingredient,
    )

    txn_type = request.GET.get("type", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    if txn_type:
        transactions = transactions.filter(transaction_type=txn_type)
    if date_from:
        try:
            transactions = transactions.filter(created_at__date__gte=timezone.datetime.strptime(date_from, "%Y-%m-%d").date())
        except ValueError:
            date_from = ""
    if date_to:
        try:
            transactions = transactions.filter(created_at__date__lte=timezone.datetime.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            date_to = ""

    return render(request, "inventory/stock_card.html", {
        "ingredient": ingredient,
        "transactions": transactions,
        "txn_type": txn_type,
        "date_from": date_from,
        "date_to": date_to,
        "types": InventoryTransaction.Type.choices,
    })


# ── Stock Movement (FR-042, FR-043, FR-044, FR-045, FR-047) ──────────


@user_passes_test(_is_manager_or_above)
def transaction_create(request):
    """Record a PURCHASE / CONSUMPTION / ADJUSTMENT / SPOILAGE / RETURN entry."""
    rid = _restaurant_id(request.user)
    form = IngredientTransactionForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        transaction = form.save()
        transaction.restaurant_id = rid
        transaction.user = request.user
        try:
            transaction.save()
        except Exception as e:
            form.add_error(None, str(e))
        else:
            sign = "in" if transaction.quantity > 0 else "out"
            messages.success(
                request,
                f"Stock movement recorded: {transaction.quantity} {transaction.ingredient.unit_of_measure} "
                f"{sign} for \"{transaction.ingredient.name}\". "
                f"Balance: {transaction.resulting_balance}.",
            )
            return redirect("inventory:stock_card", pk=transaction.ingredient.pk)
    return render(request, "inventory/transaction_form.html", {"form": form})
