"""FR-072..FR-074, FR-085, FR-086, FR-100..FR-105, BR-001..BR-005, BR-008.

Business-critical service functions for orders, payments, and receipts.
All money- and stock-affecting operations run inside atomic transactions.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import User
from inventory.models import InventoryTransaction

from .models import DiningTable, Order, Payment, round_money

TWO_PLACES = Decimal("0.01")


def is_day_locked(restaurant_id, business_date):
    """BR-008: closed business days reject new orders, payments, expenses."""
    from closing.models import DailyClosing

    return DailyClosing.objects.filter(
        restaurant_id=restaurant_id,
        business_date=business_date,
        status=DailyClosing.Status.CLOSED,
    ).exists()


def assert_day_open(restaurant_id, business_date):
    if is_day_locked(restaurant_id, business_date):
        raise ValidationError(
            "This business day is closed. Only the Owner can reopen it (Daily Closing)."
        )


# ── Payments (FR-100..FR-102, BR-005) ────────────────────────────────


def record_payment(order, method, amount, user, reference_no="", tendered=None):
    """Record a payment against an order. Overpayment is allowed only for
    CASH (change computed). Non-cash requires a reference number."""
    assert_day_open(order.restaurant_id, order.business_date)

    amount = Decimal(amount)
    if amount <= 0:
        raise ValidationError("Payment amount must be greater than zero.")
    if method != Payment.Method.CASH and not reference_no.strip():
        raise ValidationError("A reference number is required for non-cash payments.")

    if amount > order.outstanding_balance and method != Payment.Method.CASH:
        raise ValidationError(
            f"Payment of ₱{amount:.2f} exceeds the outstanding balance of "
            f"₱{order.outstanding_balance:.2f}. Overpayment is allowed for cash only."
        )

    change = Decimal("0")
    if method == Payment.Method.CASH and tendered is not None:
        tendered = Decimal(tendered)
        if tendered < amount:
            raise ValidationError("Amount tendered cannot be less than the payment amount.")
        change = round_money(tendered - amount)

    return Payment.objects.create(
        restaurant_id=order.restaurant_id,
        order=order,
        method=method,
        amount=round_money(amount),
        tendered=round_money(tendered) if tendered is not None else None,
        change_given=change,
        reference_no=reference_no.strip(),
        received_by=user,
        business_date=order.business_date,
    )


def refund_payment(payment, user, reason):
    """FR-105: negative payment linked to the original. O/M enforced in views."""
    if not reason.strip():
        raise ValidationError("A reason is required for refunds.")
    if payment.amount <= 0:
        raise ValidationError("Only positive payments can be refunded.")
    return Payment.objects.create(
        restaurant_id=payment.restaurant_id,
        order=payment.order,
        method=payment.method,
        amount=-round_money(payment.amount),
        reference_no=payment.reference_no,
        refund_of=payment,
        refund_reason=reason.strip(),
        received_by=user,
        business_date=payment.business_date,
    )


# ── Stock deduction (FR-072, FR-073, FR-074, BR-001, BR-004) ─────────


def recipe_lines_for(menu_item, addons):
    """Yield (ingredient, quantity_per_unit) tuples for an order item.
    addons is a queryset of OrderItemAddon snapshot lines."""
    from recipes.models import Recipe

    lines = []
    recipe = Recipe.get_for(menu_item=menu_item)
    if recipe:
        lines.extend((line.ingredient, line.quantity) for line in recipe.lines.all())
    for addon_line in addons:
        recipe = Recipe.get_for(addon=addon_line.addon)
        if recipe:
            lines.extend((line.ingredient, line.quantity) for line in recipe.lines.all())
    return lines


def required_ingredients(order):
    """Aggregated (ingredient → quantity) needed to complete the order."""
    needed = {}
    for item in order.items.all():
        lines = recipe_lines_for(item.menu_item, item.addons.all())
        for ingredient, qty in lines:
            needed[ingredient] = needed.get(ingredient, Decimal("0")) + qty * item.quantity
    return needed


def projected_shortfalls(order):
    """FR-074: non-blocking warning at order creation."""
    shortages = []
    for ingredient, qty in required_ingredients(order).items():
        if ingredient.current_stock < qty:
            shortages.append((ingredient, ingredient.current_stock, qty))
    return shortages


def deduct_recipe_stock(order, user):
    """FR-072: create CONSUMPTION transactions for every recipe ingredient,
    multiplied by ordered quantity, including add-ons."""
    consumed = []
    for item in order.items.all():
        for ingredient, qty in recipe_lines_for(item.menu_item, item.addons.all()):
            total = qty * item.quantity
            txn = InventoryTransaction(
                ingredient=ingredient,
                transaction_type=InventoryTransaction.Type.CONSUMPTION,
                quantity=-total,
                reference=order.order_number,
                reason=f"Order {order.order_number} — {item.item_name}",
                user=user,
            )
            txn.save()  # raises ValidationError (FR-073/BR-001) if stock would go negative
            consumed.append(txn)
    return consumed


# ── Completion & cancellation (FR-085, FR-086) ───────────────────────


@transaction.atomic
def settle_order(order, user, notify_service=None):
    """UC-03: in one transaction — verify payment covers total, deduct recipe
    stock, mark COMPLETED, assign receipt serial. Returns the order.

    Raises ValidationError (listing insufficient ingredients) on any shortage;
    the transaction rolls back so no partial state survives (NFR-012).
    """
    if order.status == Order.Status.COMPLETED:
        raise ValidationError("This order is already completed.")
    if order.status == Order.Status.CANCELLED:
        raise ValidationError("Cancelled orders cannot be completed.")

    if order.discount_needs_approval:
        raise ValidationError("This discount requires Owner/Manager approval first.")

    if not order.is_settled:
        raise ValidationError(
            f"Order is not fully paid: outstanding balance ₱{order.outstanding_balance:.2f}."
        )

    # FR-073/BR-001: check before deducting so the error lists all shortages.
    shortages = projected_shortfalls(order)
    if shortages:
        details = "; ".join(
            f"\"{ing.name}\" needs {need}, only {have} available"
            for ing, have, need in shortages
        )
        raise ValidationError(
            f"Order cannot be completed — insufficient stock: {details}"
        )

    deduct_recipe_stock(order, user)

    order.transition_to(Order.Status.COMPLETED, user)

    # FR-103: sequential receipt serial per restaurant.
    last = (
        Order.objects.filter(restaurant_id=order.restaurant_id, receipt_no__isnull=False)
        .order_by("-receipt_no")
        .values_list("receipt_no", flat=True)
        .first()
    )
    order.receipt_no = (last or 0) + 1
    order.save(update_fields=["receipt_no"])

    # FR-091: free the table when no open orders remain (staff then confirms cleaning).
    _free_table_if_idle(order, user, "Order completed")

    if notify_service:
        notify_service.order_completed(order)
    return order


@transaction.atomic
def cancel_order(order, user, reason):
    """UC-04/FR-086/BR-003: require reason; restore consumed inventory with
    compensating ADJUSTMENT entries referencing the order."""
    if order.status == Order.Status.COMPLETED:
        raise ValidationError(
            "Completed orders are immutable — use the refund flow instead (FR-105)."
        )
    if not reason.strip():
        raise ValidationError("A cancellation reason is required (FR-086).")
    assert_day_open(order.restaurant_id, order.business_date)

    consumed = InventoryTransaction.objects.filter(
        restaurant_id=order.restaurant_id,
        reference=order.order_number,
        transaction_type=InventoryTransaction.Type.CONSUMPTION,
    )
    restored = 0
    for txn in consumed:
        InventoryTransaction.objects.create(
            restaurant_id=order.restaurant_id,
            ingredient=txn.ingredient,
            transaction_type=InventoryTransaction.Type.ADJUSTMENT,
            quantity=-txn.quantity,  # reverse of consumption
            reference=order.order_number,
            reason=f"Restore for cancelled order {order.order_number}",
            user=user,
        )
        restored += 1

    order.cancel_reason = reason.strip()
    order.cancelled_by = user
    order.save(update_fields=["cancel_reason", "cancelled_by"])
    order.transition_to(Order.Status.CANCELLED, user)

    # FR-091: free the table when no open orders remain.
    _free_table_if_idle(order, user, "Order cancelled")

    return restored


def _free_table_if_idle(order, user, reason):
    """FR-091: a table becomes CLEANING once its last open order finishes;
    staff confirm CLEANING → AVAILABLE on the tables screen."""
    table = order.table
    if table is None or table.open_orders.exists():
        return
    table.set_status(DiningTable.Status.CLEANING, user, reason)


# ── Receipt payload (FR-103) ─────────────────────────────────────────


def receipt_context(order, reprint=False):
    """BIR-compliant receipt data: restaurant details + tax breakdown."""
    restaurant = order.created_by.restaurant if order.created_by else None
    return {
        "order": order,
        "restaurant": restaurant,
        "items": order.items.prefetch_related("addons").all(),
        "payments": order.payments.all(),
        "reprint": reprint,
    }
