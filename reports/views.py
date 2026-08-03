from collections import OrderedDict
from datetime import date
from decimal import Decimal

import csv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from expenses.models import Expense
from inventory.models import Ingredient, InventoryTransaction
from menu.models import Category, MenuItem
from orders.models import Order, Payment
from suppliers.models import PurchaseOrder, SupplierPayment

TWO = Decimal("0.01")


def _money(values):
    return (sum(values, Decimal("0")) if values else Decimal("0")).quantize(TWO)


def _parse_date(value, default):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return default


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _completed_orders(restaurant_id, start, end):
    """FR-139: figures come only from immutable records — COMPLETED orders
    and their payments."""
    return Order.objects.filter(
        restaurant_id=restaurant_id,
        status=Order.Status.COMPLETED,
        business_date__gte=start,
        business_date__lte=end,
    )


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


# ── FR-130: Daily Sales ─────────────────────────────────────────────

def _daily_sales_data(restaurant_id, day):
    orders = _completed_orders(restaurant_id, day, day)
    payments = Payment.objects.filter(
        restaurant_id=restaurant_id,
        business_date=day,
        order__status=Order.Status.COMPLETED,
    )
    gross = _money(o.subtotal for o in orders)
    discounts = _money(o.discount_amount for o in orders)
    net = _money(o.total for o in orders)
    vat = _money(o.vat_amount for o in orders)
    vatable = _money(o.vatable_sales for o in orders)
    exempt = _money(o.vat_exempt_sales for o in orders)
    refunds = _money(p.amount for p in payments.filter(amount__lt=0))
    method_breakdown = OrderedDict()
    for method in Payment.Method.values:
        method_breakdown[Payment.Method(method).label] = _money(
            p.amount for p in payments.filter(method=method, amount__gt=0)
        )
    cancelled = Order.objects.filter(
        restaurant_id=restaurant_id, business_date=day,
        status=Order.Status.CANCELLED,
    ).count()
    order_count = orders.count()
    aov = (net / order_count).quantize(TWO) if order_count else Decimal("0")
    return {
        "day": day,
        "gross": gross, "discounts": discounts, "net": net,
        "vatable": vatable, "exempt": exempt, "vat": vat,
        "refunds": refunds, "order_count": order_count, "aov": aov,
        "cancelled": cancelled, "method_breakdown": method_breakdown,
    }


# ── FR-132: Monthly Sales ───────────────────────────────────────────

def _monthly_data(restaurant_id, month):
    year, mon = month.year, month.month
    start = date(year, mon, 1)
    next_month = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    end = next_month - timezone.timedelta(days=1)
    prev_end = start - timezone.timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    totals = {i: Decimal("0") for i in range(1, 32)}
    prev_totals = {i: Decimal("0") for i in range(1, 32)}
    for r in _completed_orders(restaurant_id, start, end).values("business_date").annotate(total=Sum("total")):
        totals[r["business_date"].day] += r["total"]
    for r in _completed_orders(restaurant_id, prev_start, prev_end).values("business_date").annotate(total=Sum("total")):
        prev_totals[r["business_date"].day] += r["total"]
    days = []
    for day in range(1, 32):
        if totals[day] or prev_totals[day]:
            prev = prev_totals[day]
            change = ((totals[day] - prev) / prev * 100).quantize(TWO) if prev else None
            days.append({"day": day, "total": totals[day], "prev": prev, "change": change})
    return {"month": month, "days": days,
            "month_total": _money(totals.values()),
            "prev_total": _money(prev_totals.values())}


# ── FR-133: Profit & Loss ───────────────────────────────────────────

def _pandl_data(restaurant_id, start, end):
    net_sales = _money(o.total for o in _completed_orders(restaurant_id, start, end))
    expenses = _money(e.amount for e in Expense.objects.filter(
        restaurant_id=restaurant_id,
        expense_date__gte=start, expense_date__lte=end,
        status=Expense.Status.APPROVED,
    ))
    consumptions = InventoryTransaction.objects.filter(
        restaurant_id=restaurant_id,
        transaction_type__in=[InventoryTransaction.Type.CONSUMPTION, InventoryTransaction.Type.SPOILAGE],
        created_at__date__gte=start, created_at__date__lte=end,
    ).select_related("ingredient")
    cogs = _money(abs(t.quantity) * t.ingredient.average_unit_cost for t in consumptions)
    profit = net_sales - cogs - expenses
    return {"net_sales": net_sales, "cogs": cogs, "expenses": expenses, "profit": profit}


# ── FR-134: Inventory ───────────────────────────────────────────────

def _inventory_data(restaurant_id, start, end):
    ingredients = Ingredient.objects.filter(restaurant_id=restaurant_id, is_deleted=False)
    usage_rows = []
    usage = InventoryTransaction.objects.filter(
        restaurant_id=restaurant_id,
        transaction_type=InventoryTransaction.Type.CONSUMPTION,
        created_at__date__gte=start, created_at__date__lte=end,
    ).values("ingredient__name").annotate(qty=Sum("quantity"), count=Count("id"))
    for u in usage:
        usage_rows.append({"name": u["ingredient__name"], "qty": u["qty"], "count": u["count"]})
    spoilage_cost = _money(t.quantity * t.ingredient.average_unit_cost for t in InventoryTransaction.objects.filter(
        restaurant_id=restaurant_id,
        transaction_type=InventoryTransaction.Type.SPOILAGE,
        created_at__date__gte=start, created_at__date__lte=end,
    ).select_related("ingredient"))
    low_stock = [i for i in ingredients if i.current_stock < i.minimum_stock]
    return {
        "ingredients": ingredients,
        "usage_rows": sorted(usage_rows, key=lambda r: -r["qty"]),
        "spoilage_cost": spoilage_cost,
        "low_stock": low_stock,
    }


# ── FR-135: Product Mix ─────────────────────────────────────────────

def _product_mix_data(restaurant_id, start, end, category_id):
    from orders.models import OrderItem

    items = OrderItem.objects.filter(
        order__restaurant_id=restaurant_id,
        order__status=Order.Status.COMPLETED,
        order__business_date__gte=start,
        order__business_date__lte=end,
    ).prefetch_related("addons")
    if category_id:
        items = items.filter(menu_item__category_id=category_id)
    totals = {}
    for item in items:
        key = item.item_name
        row = totals.setdefault(key, {"item_name": key, "qty": Decimal("0"), "revenue": Decimal("0"), "count": 0})
        row["qty"] += item.quantity
        row["revenue"] += item.line_total
        row["count"] += 1
    rows = sorted(totals.values(), key=lambda r: -r["revenue"])
    return {"rows": rows, "category_id": category_id}


# ── FR-136: Purchase Report ─────────────────────────────────────────

def _purchase_data(restaurant_id, start, end, supplier_id):
    pos = PurchaseOrder.objects.filter(
        restaurant_id=restaurant_id,
        created_at__date__gte=start, created_at__date__lte=end,
    ).select_related("supplier")
    if supplier_id:
        pos = pos.filter(supplier_id=supplier_id)
    rows = []
    for po in pos:
        rows.append({
            "po": po, "supplier": po.supplier.name,
            "total": po.total, "received": po.received_total,
            "outstanding": po.supplier.outstanding_balance.quantize(TWO),
        })
    total_received = _money(r["received"] for r in rows)
    total_outstanding = _money(r["outstanding"] for r in rows)
    return {"rows": rows, "total_received": total_received, "total_outstanding": total_outstanding}


# ── FR-137: Tax Summary ─────────────────────────────────────────────

def _tax_data(restaurant_id, start, end):
    orders = _completed_orders(restaurant_id, start, end)
    return {
        "vatable": _money(o.vatable_sales for o in orders),
        "exempt": _money(o.vat_exempt_sales for o in orders),
        "output_vat": _money(o.vat_amount for o in orders),
        "discounts": _money(o.discount_amount for o in orders),
    }


# ── Views ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_manager_or_above)
def daily_sales(request):
    day = _parse_date(request.GET.get("date"), timezone.localdate())
    data = _daily_sales_data(request.user.restaurant_id, day)
    if request.GET.get("export"):
        rows = [
            ("Business date", day),
            ("Gross sales", data["gross"]), ("Discounts", data["discounts"]),
            ("Net sales", data["net"]), ("VATable sales", data["vatable"]),
            ("VAT-exempt sales", data["exempt"]), ("Output VAT", data["vat"]),
            ("Order count", data["order_count"]), ("Average order value", data["aov"]),
            ("Cancelled orders", data["cancelled"]), ("Refunds", data["refunds"]),
        ]
        for method, amount in data["method_breakdown"].items():
            rows.append((f"{method} sales", amount))
        return _csv_response(f"daily_sales_{day}.csv", ["metric", "value"], rows)
    return render(request, "reports/daily_sales.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def monthly_sales(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    mon = int(request.GET.get("month", today.month))
    month = date(year, mon, 1)
    data = _monthly_data(request.user.restaurant_id, month)
    if request.GET.get("export"):
        rows = [(d["day"], d["total"], d["prev"]) for d in data["days"]]
        return _csv_response(f"monthly_sales_{month:%Y-%m}.csv",
                             ["day", "sales", "previous_month_sales"], rows)
    return render(request, "reports/monthly_sales.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def profit_loss(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get("start"), today.replace(day=1))
    end = _parse_date(request.GET.get("end"), today)
    data = _pandl_data(request.user.restaurant_id, start, end)
    data.update({"start": start, "end": end})
    if request.GET.get("export"):
        rows = [("Net sales", data["net_sales"]), ("Cost of goods", data["cogs"]),
                ("Expenses", data["expenses"]), ("Profit", data["profit"])]
        return _csv_response(f"profit_loss_{start}_{end}.csv", ["metric", "value"], rows)
    return render(request, "reports/profit_loss.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def inventory_report(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get("start"), today.replace(day=1))
    end = _parse_date(request.GET.get("end"), today)
    data = _inventory_data(request.user.restaurant_id, start, end)
    data.update({"start": start, "end": end})
    if request.GET.get("export"):
        rows = [(i.name, i.unit_of_measure, i.current_stock, i.minimum_stock,
                 i.average_unit_cost) for i in data["ingredients"]]
        return _csv_response(f"inventory_{start}_{end}.csv",
                             ["ingredient", "unit", "current_stock", "minimum_stock", "avg_cost"], rows)
    return render(request, "reports/inventory_report.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def product_mix(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get("start"), today.replace(day=1))
    end = _parse_date(request.GET.get("end"), today)
    category_id = request.GET.get("category") or None
    data = _product_mix_data(request.user.restaurant_id, start, end, category_id)
    data.update({"start": start, "end": end,
                 "categories": Category.objects.filter(restaurant_id=request.user.restaurant_id)})
    if request.GET.get("export"):
        rows = [list(r.values()) for r in data["rows"]]
        return _csv_response("product_mix.csv", ["item", "qty", "revenue", "orders"], rows)
    return render(request, "reports/product_mix.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def purchase_report(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get("start"), today.replace(day=1))
    end = _parse_date(request.GET.get("end"), today)
    supplier_id = request.GET.get("supplier") or None
    data = _purchase_data(request.user.restaurant_id, start, end, supplier_id)
    data.update({"start": start, "end": end,
                 "suppliers": PurchaseOrder.objects.filter(restaurant_id=request.user.restaurant_id)
                     .values_list("supplier_id", "supplier__name").distinct()})
    if request.GET.get("export"):
        rows = [(r["po"].po_number, r["supplier"], r["po"].get_status_display(),
                 r["total"], r["received"], r["outstanding"]) for r in data["rows"]]
        return _csv_response(f"purchases_{start}_{end}.csv",
                             ["po_number", "supplier", "status", "total", "received", "outstanding"], rows)
    return render(request, "reports/purchase_report.html", {"data": data})


@login_required
@user_passes_test(_is_manager_or_above)
def tax_summary(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get("start"), today.replace(day=1))
    end = _parse_date(request.GET.get("end"), today)
    data = _tax_data(request.user.restaurant_id, start, end)
    data.update({"start": start, "end": end})
    if request.GET.get("export"):
        rows = [("VATable sales", data["vatable"]), ("VAT-exempt sales", data["exempt"]),
                ("Output VAT", data["output_vat"]), ("Discounts", data["discounts"])]
        return _csv_response(f"tax_summary_{start}_{end}.csv", ["metric", "value"], rows)
    return render(request, "reports/tax_summary.html", {"data": data})
