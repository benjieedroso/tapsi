from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from inventory.models import InventoryTransaction

from .forms import PurchaseOrderForm, SupplierForm, SupplierPaymentForm
from .models import PurchaseOrder, PurchaseOrderItem, Supplier, SupplierPayment


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


# ── Suppliers (FR-050..FR-053) ───────────────────────────────────────


@user_passes_test(_is_manager_or_above)
def supplier_list(request):
    rid = _restaurant_id(request.user)
    q = request.GET.get("q", "").strip()
    suppliers = Supplier.objects.filter(restaurant_id=rid, is_deleted=False)
    if q:
        suppliers = suppliers.filter(name__icontains=q)
    return render(request, "suppliers/supplier_list.html", {"suppliers": suppliers, "q": q})


@user_passes_test(_is_manager_or_above)
def supplier_detail(request, pk):
    rid = _restaurant_id(request.user)
    supplier = get_object_or_404(Supplier, pk=pk, restaurant_id=rid, is_deleted=False)
    # FR-051: purchase history + computed outstanding balance.
    pos = supplier.purchase_orders.prefetch_related("items")
    payment_form = SupplierPaymentForm(restaurant_id=rid)
    return render(request, "suppliers/supplier_detail.html", {
        "supplier": supplier,
        "pos": pos,
        "payment_form": payment_form,
    })


@user_passes_test(_is_manager_or_above)
def supplier_create(request):
    rid = _restaurant_id(request.user)
    form = SupplierForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        supplier = form.save(commit=False)
        supplier.restaurant_id = rid
        supplier.save()
        messages.success(request, f"Supplier \"{supplier.name}\" created.")
        return redirect("suppliers:supplier_list")
    return render(request, "suppliers/supplier_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def supplier_edit(request, pk):
    rid = _restaurant_id(request.user)
    supplier = get_object_or_404(Supplier, pk=pk, restaurant_id=rid, is_deleted=False)
    form = SupplierForm(request.POST or None, instance=supplier, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Supplier \"{supplier.name}\" updated.")
        return redirect("suppliers:supplier_detail", pk=supplier.pk)
    return render(request, "suppliers/supplier_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def supplier_delete(request, pk):
    """FR-053: deactivate rather than delete when POs exist."""
    rid = _restaurant_id(request.user)
    supplier = get_object_or_404(Supplier, pk=pk, restaurant_id=rid, is_deleted=False)
    if supplier.has_purchase_orders:
        supplier.soft_delete()
        messages.success(request, f"Supplier \"{supplier.name}\" deactivated (has purchase history).")
    else:
        supplier.delete()
        messages.success(request, f"Supplier \"{supplier.name}\" deleted.")
    return redirect("suppliers:supplier_list")


@user_passes_test(_is_manager_or_above)
@require_POST
def supplier_payment_create(request, pk):
    """FR-052: record a payment against received POs."""
    rid = _restaurant_id(request.user)
    supplier = get_object_or_404(Supplier, pk=pk, restaurant_id=rid, is_deleted=False)
    form = SupplierPaymentForm(request.POST or None, restaurant_id=rid)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.restaurant_id = rid
        payment.supplier = supplier
        payment.recorded_by = request.user
        payment.save()
        messages.success(request, f"Payment of ₱{payment.amount} recorded for \"{supplier.name}\".")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("suppliers:supplier_detail", pk=supplier.pk)


# ── Purchase Orders (FR-060..FR-065) ─────────────────────────────────


@user_passes_test(_is_manager_or_above)
def po_list(request):
    rid = _restaurant_id(request.user)
    pos = PurchaseOrder.objects.filter(restaurant_id=rid).select_related("supplier")
    status = request.GET.get("status", "")
    supplier_id = request.GET.get("supplier", "")
    if status:
        pos = pos.filter(status=status)
    if supplier_id:
        pos = pos.filter(supplier_id=supplier_id)
    suppliers = Supplier.objects.filter(restaurant_id=rid, is_deleted=False)
    return render(request, "suppliers/po_list.html", {
        "pos": pos, "suppliers": suppliers,
        "status": status, "supplier_id": supplier_id,
    })


@user_passes_test(_is_manager_or_above)
def po_create(request):
    rid = _restaurant_id(request.user)
    form = PurchaseOrderForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        po = form.save(commit=False)
        po.restaurant_id = rid
        po.placed_by = request.user
        po.save()
        ingredient = form.cleaned_data.get("line_ingredient")
        if ingredient is not None:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                ingredient=ingredient,
                qty_ordered=form.cleaned_data["line_quantity"],
                unit_cost=form.cleaned_data["line_unit_cost"],
            )
        messages.success(request, f"Purchase order {po.po_number} created.")
        return redirect("suppliers:po_detail", pk=po.pk)
    return render(request, "suppliers/po_form.html", {"form": form})


@user_passes_test(_is_manager_or_above)
def po_detail(request, pk):
    rid = _restaurant_id(request.user)
    po = get_object_or_404(PurchaseOrder, pk=pk, restaurant_id=rid)
    return render(request, "suppliers/po_detail.html", {
        "po": po,
        "variance": po.total - po.received_total,
    })


@user_passes_test(_is_manager_or_above)
def po_edit(request, pk):
    """FR-064: editable only while DRAFT."""
    rid = _restaurant_id(request.user)
    po = get_object_or_404(PurchaseOrder, pk=pk, restaurant_id=rid)
    if po.status != PurchaseOrder.Status.DRAFT:
        messages.error(request, "Only draft purchase orders can be edited.")
        return redirect("suppliers:po_detail", pk=po.pk)
    form = PurchaseOrderForm(request.POST or None, instance=po, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        ingredient = form.cleaned_data.get("line_ingredient")
        if ingredient is not None:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                ingredient=ingredient,
                qty_ordered=form.cleaned_data["line_quantity"],
                unit_cost=form.cleaned_data["line_unit_cost"],
            )
        messages.success(request, f"{po.po_number} updated.")
        return redirect("suppliers:po_detail", pk=po.pk)
    return render(request, "suppliers/po_form.html", {"form": form})


@user_passes_test(_is_manager_or_above)
@require_POST
def po_place(request, pk):
    """DRAFT → ORDERED (FR-061)."""
    rid = _restaurant_id(request.user)
    po = get_object_or_404(PurchaseOrder, pk=pk, restaurant_id=rid)
    if po.status == PurchaseOrder.Status.DRAFT and po.items.exists():
        po.status = PurchaseOrder.Status.ORDERED
        po.save(update_fields=["status"])
        messages.success(request, f"{po.po_number} placed.")
    else:
        messages.error(request, "Only drafts with line items can be placed.")
    return redirect("suppliers:po_detail", pk=po.pk)


@user_passes_test(_is_manager_or_above)
@require_POST
def po_cancel(request, pk):
    """FR-061: CANCELLED allowed from DRAFT or ORDERED."""
    rid = _restaurant_id(request.user)
    po = get_object_or_404(PurchaseOrder, pk=pk, restaurant_id=rid)
    if po.status in {PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.ORDERED}:
        po.status = PurchaseOrder.Status.CANCELLED
        po.save(update_fields=["status"])
        messages.success(request, f"{po.po_number} cancelled.")
    else:
        messages.error(request, f"{po.po_number} cannot be cancelled from its current status.")
    return redirect("suppliers:po_detail", pk=po.pk)


@user_passes_test(_is_manager_or_above)
def po_receive(request, pk):
    """FR-062/FR-065: enter received quantity per line (≤ outstanding);
    creates PURCHASE transactions atomically and updates status."""
    rid = _restaurant_id(request.user)
    po = get_object_or_404(PurchaseOrder, pk=pk, restaurant_id=rid)
    if po.status not in {PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED}:
        messages.error(request, "Only ordered POs can be received.")
        return redirect("suppliers:po_detail", pk=po.pk)

    errors = []
    if request.method == "POST":
        with transaction.atomic():
            for item in po.items.all():
                raw = request.POST.get(f"received_{item.pk}", "").strip()
                if not raw:
                    continue
                try:
                    qty = Decimal(raw)
                except Exception:
                    errors.append(f"{item.ingredient.name}: invalid quantity.")
                    continue
                if qty <= 0:
                    errors.append(f"{item.ingredient.name}: quantity must be positive.")
                    continue
                if qty > item.outstanding_qty:
                    errors.append(
                        f"{item.ingredient.name}: received {qty} exceeds outstanding {item.outstanding_qty}."
                    )
                    continue
                # FR-062: PURCHASE transaction feeds inventory + weighted average cost.
                txn = InventoryTransaction(
                    ingredient=item.ingredient,
                    transaction_type=InventoryTransaction.Type.PURCHASE,
                    quantity=qty,
                    unit_cost=item.unit_cost,
                    reference=po.po_number,
                    user=request.user,
                )
                txn.save()
                item.qty_received += qty
                item.save(update_fields=["qty_received"])
        if errors:
            for error in errors:
                messages.error(request, error)
        po.refresh_from_db()
        all_received = all(i.qty_received >= i.qty_ordered for i in po.items.all())
        any_received = any(i.qty_received > 0 for i in po.items.all())
        if any_received:
            po.status = (
                PurchaseOrder.Status.RECEIVED
                if all_received
                else PurchaseOrder.Status.PARTIALLY_RECEIVED
            )
            po.save(update_fields=["status"])
            from notifications.services import Notifier
            Notifier().po_received(po)
            messages.success(
                request,
                f"{po.po_number} received — stock updated." if all_received
                else f"{po.po_number} partially received — stock updated.",
            )
        return redirect("suppliers:po_detail", pk=po.pk)

    return render(request, "suppliers/po_receive.html", {"po": po})
