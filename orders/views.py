from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from menu.models import AddOn, MenuItem

from . import services
from .forms import (
    DiscountForm, OrderItemForm, OrderForm, PaymentForm, RefundForm, TableForm,
)
from .models import (
    DiningTable, Order, OrderItem, OrderItemAddon, Payment,
    business_date_today, generate_order_number,
)


def _is_staff(user):
    return user.is_authenticated and user.role in {
        User.Role.OWNER, User.Role.MANAGER, User.Role.CASHIER,
    }


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _is_kitchen_or_above(user):
    return user.is_authenticated and user.role in {
        User.Role.OWNER, User.Role.MANAGER, User.Role.KITCHEN,
    }


def _restaurant_id(user):
    return user.restaurant_id


def _notify():
    """Lazy import to avoid app-order dependency issues."""
    from notifications.services import Notifier
    return Notifier()


# ── Tables (FR-090..FR-095) ──────────────────────────────────────────


@user_passes_test(_is_staff)
def table_list(request):
    rid = _restaurant_id(request.user)
    tables = DiningTable.objects.filter(restaurant_id=rid, is_active=True)
    return render(request, "orders/table_list.html", {"tables": tables})


@user_passes_test(_is_manager_or_above)
def table_create(request):
    rid = _restaurant_id(request.user)
    form = TableForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        table = form.save(commit=False)
        table.restaurant_id = rid
        table.save()
        messages.success(request, f"Table \"{table.name}\" created.")
        return redirect("orders:table_list")
    return render(request, "orders/table_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def table_edit(request, pk):
    rid = _restaurant_id(request.user)
    table = get_object_or_404(DiningTable, pk=pk, restaurant_id=rid)
    form = TableForm(request.POST or None, instance=table, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Table \"{table.name}\" updated.")
        return redirect("orders:table_list")
    return render(request, "orders/table_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def table_delete(request, pk):
    rid = _restaurant_id(request.user)
    table = get_object_or_404(DiningTable, pk=pk, restaurant_id=rid)
    if table.open_orders.exists():
        messages.error(request, "Cannot delete a table with open orders.")
        return redirect("orders:table_list")
    table.delete()
    messages.success(request, f"Table \"{table.name}\" deleted.")
    return redirect("orders:table_list")


@user_passes_test(_is_staff)
@require_POST
def table_status(request, pk):
    """FR-092: staff confirm CLEANING → AVAILABLE; O/M set any status."""
    rid = _restaurant_id(request.user)
    table = get_object_or_404(DiningTable, pk=pk, restaurant_id=rid)
    new_status = request.POST.get("status", "")
    if new_status not in DiningTable.Status.values:
        messages.error(request, "Invalid status.")
        return redirect("orders:table_list")
    if new_status == DiningTable.Status.AVAILABLE and table.open_orders.exists():
        messages.error(request, "Table has open orders; it cannot be set available.")
        return redirect("orders:table_list")
    if not _is_manager_or_above(request.user):
        # Cashiers may only mark CLEANING → AVAILABLE.
        allowed = {DiningTable.Status.CLEANING: DiningTable.Status.AVAILABLE}
        if allowed.get(table.status) != new_status:
            messages.error(request, "Cashiers can only confirm cleaning is done.")
            return redirect("orders:table_list")
    table.set_status(new_status, request.user)
    messages.success(request, f"Table \"{table.name}\" is now {table.get_status_display()}.")
    return redirect("orders:table_list")


# ── Orders (FR-080..FR-089) ──────────────────────────────────────────


@user_passes_test(_is_staff)
def order_list(request):
    rid = _restaurant_id(request.user)
    orders = Order.objects.filter(restaurant_id=rid).select_related("table", "created_by")
    status = request.GET.get("status", "")
    order_type = request.GET.get("type", "")
    if status:
        orders = orders.filter(status=status)
    if order_type:
        orders = orders.filter(order_type=order_type)
    return render(request, "orders/order_list.html", {
        "orders": orders, "status": status, "order_type": order_type,
    })


@user_passes_test(_is_staff)
def order_create(request):
    rid = _restaurant_id(request.user)
    form = OrderForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        try:
            services.assert_day_open(rid, business_date_today())
            order = Order(
                restaurant_id=rid,
                order_type=form.cleaned_data["order_type"],
                table=form.cleaned_data.get("table"),
                customer_name=form.cleaned_data.get("customer_name", "").strip(),
                customer_phone=form.cleaned_data.get("customer_phone", "").strip(),
                customer_address=form.cleaned_data.get("customer_address", "").strip(),
                created_by=request.user,
            )
            order.order_number = generate_order_number(rid, order.business_date)
            order.save()
            # FR-092: dine-in sets table OCCUPIED.
            if order.table:
                order.table.set_status(DiningTable.Status.OCCUPIED, request.user, "Order created")
            messages.success(request, f"Order {order.order_number} created.")
            _notify().order_placed(order)
            return redirect("orders:order_detail", pk=order.pk)
        except ValidationError as e:
            for message in e.messages if hasattr(e, "messages") else [str(e)]:
                messages.error(request, message)
    return render(request, "orders/order_form.html", {"form": form})


@user_passes_test(_is_staff)
def order_detail(request, pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    item_form = OrderItemForm(restaurant_id=rid)
    payment_form = PaymentForm()
    discount_form = DiscountForm()
    available_tables = DiningTable.objects.filter(
        restaurant_id=rid,
        status__in=[DiningTable.Status.AVAILABLE, DiningTable.Status.CLEANING],
        is_active=True,
    ).exclude(pk=order.table_id).order_by("name")
    # FR-074: non-blocking projected stock warning.
    shortfalls = services.projected_shortfalls(order)
    return render(request, "orders/order_detail.html", {
        "order": order,
        "item_form": item_form,
        "payment_form": payment_form,
        "discount_form": discount_form,
        "available_tables": available_tables,
        "shortfalls": shortfalls,
    })


@user_passes_test(_is_staff)
def order_item_add(request, pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    form = OrderItemForm(request.POST or None, restaurant_id=rid)
    if order.status != Order.Status.PENDING:
        messages.error(request, "Only PENDING orders can have items added (FR-084).")
        return redirect("orders:order_detail", pk=order.pk)
    if form.is_valid():
        try:
            menu_item = form.cleaned_data["menu_item"]
            if not menu_item.is_available:
                raise ValidationError(f"\"{menu_item.name}\" is unavailable.")
            item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=menu_item.name,
                unit_price=menu_item.price,
                quantity=form.cleaned_data["quantity"],
                notes=form.cleaned_data.get("notes", "").strip(),
            )
            for addon in form.cleaned_data["addons"]:
                OrderItemAddon.objects.create(
                    order_item=item, addon=addon,
                    addon_name=addon.name, price=addon.price,
                )
            order.recompute_totals()
            messages.success(request, f"Added \"{item.item_name}\" × {item.quantity}.")
        except ValidationError as e:
            for message in e.messages if hasattr(e, "messages") else [str(e)]:
                messages.error(request, message)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
def order_item_edit(request, pk, item_pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    if order.status != Order.Status.PENDING:
        messages.error(request, "Only PENDING orders can be edited (FR-084).")
        return redirect("orders:order_detail", pk=order.pk)
    form = OrderItemForm(request.POST or None, restaurant_id=rid, instance=item)
    if form.is_valid():
        item.quantity = form.cleaned_data["quantity"]
        item.notes = form.cleaned_data.get("notes", "").strip()
        item.save()
        # Replace add-ons with the selected set.
        item.addons.all().delete()
        for addon in form.cleaned_data["addons"]:
            OrderItemAddon.objects.create(
                order_item=item, addon=addon, addon_name=addon.name, price=addon.price,
            )
        order.recompute_totals()
        messages.success(request, f"\"{item.item_name}\" updated.")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
@require_POST
def order_item_remove(request, pk, item_pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    if order.status != Order.Status.PENDING:
        messages.error(request, "Only PENDING orders can be edited (FR-084).")
        return redirect("orders:order_detail", pk=order.pk)
    item.delete()
    order.recompute_totals()
    messages.success(request, f"Removed \"{item.item_name}\".")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
@require_POST
def order_discount(request, pk):
    """FR-087: Senior/PWD 20% + ID capture; manual >10% needs approval."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    form = DiscountForm(request.POST)
    if form.is_valid():
        try:
            order.apply_discount(
                form.cleaned_data["discount_type"],
                discount_ref=form.cleaned_data.get("discount_ref", ""),
                pct=form.cleaned_data.get("manual_discount_pct"),
                user=request.user,
            )
            messages.success(request, f"Discount of ₱{order.discount_amount:.2f} applied.")
            if order.discount_needs_approval:
                messages.warning(request, "Manual discount above 10% requires Owner/Manager approval.")
            _notify().large_discount(order, request.user)
        except ValidationError as e:
            for message in e.messages if hasattr(e, "messages") else [str(e)]:
                messages.error(request, message)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_manager_or_above)
@require_POST
def order_discount_approve(request, pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    try:
        order.approve_discount(request.user)
        messages.success(request, "Discount approved.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_manager_or_above)
@require_POST
def order_cancel(request, pk):
    """FR-086: cancel with reason; restores consumed stock (BR-003)."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    reason = request.POST.get("reason", "").strip()
    try:
        restored = services.cancel_order(order, request.user, reason)
        _notify().order_cancelled(order)
        msg = f"Order {order.order_number} cancelled."
        if restored:
            msg += f" {restored} inventory transactions restored."
        messages.success(request, msg)
    except ValidationError as e:
        for message in e.messages if hasattr(e, "messages") else [str(e)]:
            messages.error(request, message)
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
@require_POST
def order_complete(request, pk):
    """FR-085/UC-03: verify payment, deduct stock, complete, receipt serial."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    try:
        services.settle_order(order, request.user, notify_service=_notify())
        messages.success(request, f"Order {order.order_number} completed.")
        return redirect("orders:receipt", pk=order.pk)
    except ValidationError as e:
        for message in e.messages if hasattr(e, "messages") else [str(e)]:
            messages.error(request, message)
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
def order_transfer(request, pk):
    """FR-093: move an open order to another AVAILABLE table."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    if order.order_type != Order.Type.DINE_IN:
        messages.error(request, "Only dine-in orders can be transferred.")
        return redirect("orders:order_detail", pk=order.pk)
    if order.status in {Order.Status.COMPLETED, Order.Status.CANCELLED}:
        messages.error(request, "Only open orders can be transferred.")
        return redirect("orders:order_detail", pk=order.pk)
    target_id = request.POST.get("table_id", "")
    target = get_object_or_404(
        DiningTable, pk=target_id, restaurant_id=rid, is_active=True,
    ) if target_id else None
    if target is None or target.pk == (order.table.pk if order.table else None):
        messages.error(request, "Choose a different table.")
        return redirect("orders:order_detail", pk=order.pk)
    if target.status == DiningTable.Status.OCCUPIED:
        messages.error(request, "Target table is occupied.")
        return redirect("orders:order_detail", pk=order.pk)
    old_table = order.table
    order.table = target
    order.save(update_fields=["table"])
    target.set_status(DiningTable.Status.OCCUPIED, request.user, "Order transferred")
    if old_table and not old_table.open_orders.exists():
        old_table.set_status(DiningTable.Status.CLEANING, request.user, "Order transferred away")
    messages.success(request, f"Order moved to table {target.name}.")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_staff)
@require_POST
def order_merge(request, pk):
    """FR-094: merge another open dine-in order into this one."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    other_id = request.POST.get("order_id", "")
    other = get_object_or_404(Order, pk=other_id, restaurant_id=rid) if other_id else None
    if other is None or other.pk == order.pk:
        messages.error(request, "Choose a different order to merge.")
        return redirect("orders:order_detail", pk=order.pk)
    if other.order_type != Order.Type.DINE_IN or order.order_type != Order.Type.DINE_IN:
        messages.error(request, "Only dine-in orders can be merged.")
        return redirect("orders:order_detail", pk=order.pk)
    if order.status != Order.Status.PENDING or other.status != Order.Status.PENDING:
        messages.error(request, "Both orders must be PENDING to merge.")
        return redirect("orders:order_detail", pk=order.pk)
    for item in other.items.all():
        item.order = order
        item.save(update_fields=["order"])
    other.table = None
    other.save(update_fields=["table"])
    other.transition_to(Order.Status.CANCELLED, request.user, "Merged into another bill")
    other.cancel_reason = f"Merged into {order.order_number}"
    other.save(update_fields=["cancel_reason"])
    order.recompute_totals()
    messages.success(request, f"{other.order_number} merged into {order.order_number}.")
    return redirect("orders:order_detail", pk=order.pk)


# ── Kitchen (FR-088, FR-089) ─────────────────────────────────────────


@user_passes_test(_is_kitchen_or_above)
def kitchen_queue(request):
    rid = _restaurant_id(request.user)
    orders = (
        Order.objects.filter(
            restaurant_id=rid,
            status__in=[Order.Status.PENDING, Order.Status.PREPARING],
        )
        .select_related("table")
        .prefetch_related("items__addons")
        .order_by("created_at")
    )
    return render(request, "orders/kitchen_queue.html", {"orders": orders})


@user_passes_test(_is_kitchen_or_above)
@require_POST
def kitchen_advance(request, pk):
    """PENDING → PREPARING → READY."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    next_status = {
        Order.Status.PENDING: Order.Status.PREPARING,
        Order.Status.PREPARING: Order.Status.READY,
    }.get(order.status)
    if next_status is None:
        messages.error(request, "Order cannot be advanced from its current status.")
        return redirect("orders:kitchen_queue")
    try:
        order.transition_to(next_status, request.user)
        messages.success(request, f"{order.order_number} is now {order.get_status_display()}.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("orders:kitchen_queue")


# ── Payments, refunds, receipts (FR-100..FR-106) ────────────────────


@user_passes_test(_is_staff)
@require_POST
def payment_create(request, pk):
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    form = PaymentForm(request.POST)
    if form.is_valid():
        try:
            payment = services.record_payment(
                order,
                form.cleaned_data["method"],
                form.cleaned_data["amount"],
                request.user,
                reference_no=form.cleaned_data.get("reference_no", ""),
                tendered=form.cleaned_data.get("tendered"),
            )
            msg = f"₱{payment.amount:.2f} received via {payment.get_method_display()}."
            if payment.change_given:
                msg += f" Change: ₱{payment.change_given:.2f}"
            if order.is_settled:
                msg += " Order is fully settled."
            messages.success(request, msg)
        except ValidationError as e:
            for message in e.messages if hasattr(e, "messages") else [str(e)]:
                messages.error(request, message)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("orders:order_detail", pk=order.pk)


@user_passes_test(_is_manager_or_above)
@require_POST
def payment_refund(request, pk):
    """FR-105: Owner/Manager only; negative payment linked to the original."""
    rid = _restaurant_id(request.user)
    payment = get_object_or_404(Payment, pk=pk, restaurant_id=rid)
    form = RefundForm(request.POST)
    if form.is_valid():
        try:
            refund = services.refund_payment(payment, request.user, form.cleaned_data["reason"])
            messages.success(request, f"Refund of ₱{refund.amount:.2f} recorded.")
            _notify().refund_issued(refund)
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect("orders:order_detail", pk=payment.order.pk)


@user_passes_test(_is_staff)
def receipt(request, pk, reprint=False):
    """FR-103/FR-104: printable BIR-compliant receipt; reprints watermarked
    and audit-logged."""
    rid = _restaurant_id(request.user)
    order = get_object_or_404(Order, pk=pk, restaurant_id=rid)
    if reprint and order.status == Order.Status.COMPLETED:
        order.receipt_reprinted_count += 1
        order.save(update_fields=["receipt_reprinted_count"])
    context = services.receipt_context(order, reprint=reprint)
    return render(request, "orders/receipt.html", context)
