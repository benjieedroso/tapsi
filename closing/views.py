from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from orders.models import Order

from .models import DailyClosing

VARIANCE_LIMIT = 100  # FR-141: ±₱100


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


@user_passes_test(_is_manager_or_above)
def closing_list(request):
    rid = _restaurant_id(request.user)
    closings = DailyClosing.objects.filter(restaurant_id=rid).select_related("closed_by")
    return render(request, "closing/closing_list.html", {"closings": closings})


@user_passes_test(_is_manager_or_above)
def closing_prepare(request):
    """FR-140 step 1-2: verify no open orders; preview expected cash."""
    rid = _restaurant_id(request.user)
    business_date = timezone.localdate()
    open_orders = Order.objects.filter(
        restaurant_id=rid,
        business_date=business_date,
        status__in=[Order.Status.PENDING, Order.Status.PREPARING, Order.Status.READY],
    )
    expected = DailyClosing.expected_cash_for(rid, business_date)
    opening_float = DailyClosing.current_float(rid)
    already_closed = DailyClosing.objects.filter(
        restaurant_id=rid, business_date=business_date,
    ).first()
    return render(request, "closing/closing_prepare.html", {
        "business_date": business_date,
        "open_orders": open_orders,
        "expected_cash": expected,
        "opening_float": opening_float,
        "already_closed": already_closed,
    })


@user_passes_test(_is_manager_or_above)
@require_POST
def closing_complete(request):
    """FR-140/141: count cash, compute variance, require explanation if
    beyond ±₱100, then lock the day (FR-142) and produce the EOD report."""
    rid = _restaurant_id(request.user)
    business_date = timezone.localdate()
    if DailyClosing.objects.filter(
        restaurant_id=rid, business_date=business_date,
    ).exists():
        messages.error(request, "This business day is already closed.")
        return redirect("closing:closing_list")

    open_orders = Order.objects.filter(
        restaurant_id=rid,
        business_date=business_date,
        status__in=[Order.Status.PENDING, Order.Status.PREPARING, Order.Status.READY],
    )
    if open_orders.exists():
        messages.error(request, "Open orders remain — complete or cancel them before closing (FR-140).")
        return redirect("closing:closing_prepare")

    try:
        from decimal import Decimal
        counted = Decimal(request.POST.get("counted_cash", ""))
    except Exception:
        messages.error(request, "Enter the counted cash amount.")
        return redirect("closing:closing_prepare")

    expected = DailyClosing.expected_cash_for(rid, business_date)
    variance = expected - counted
    note = request.POST.get("variance_note", "").strip()
    if abs(variance) > VARIANCE_LIMIT and not note:
        messages.error(request, "Variance beyond ±₱100 requires a written explanation (FR-141).")
        return redirect("closing:closing_prepare")

    closing = DailyClosing.objects.create(
        restaurant_id=rid,
        business_date=business_date,
        opening_float=DailyClosing.current_float(rid),
        expected_cash=expected,
        counted_cash=counted,
        variance=variance,
        variance_note=note,
        status=DailyClosing.Status.CLOSED,
        closed_by=request.user,
    )
    from audit_logs.services import log
    log(
        actor=request.user, action="DAY_CLOSE", entity="daily_closing",
        entity_id=closing.pk,
        after={"business_date": str(business_date), "variance": str(variance)},
        request=request,
    )
    messages.success(
        request,
        f"Business day closed. Variance: ₱{variance:.2f}. "
        f"Day locked: no orders, payments, or expenses may be added (FR-142).",
    )
    return redirect("closing:eod_report", pk=closing.pk)


@user_passes_test(_is_manager_or_above)
def eod_report(request, pk):
    """FR-143: End-of-Day report — Z-Reading + expense summary + variance."""
    rid = _restaurant_id(request.user)
    closing = get_object_or_404(DailyClosing, pk=pk, restaurant_id=rid)
    return render(request, "closing/eod_report.html", {"closing": closing})


@user_passes_test(lambda u: u.is_authenticated and u.role == User.Role.OWNER)
@require_POST
def closing_reopen(request, pk):
    """FR-144: only the Owner may reopen; reason required; audit-logged."""
    rid = _restaurant_id(request.user)
    closing = get_object_or_404(DailyClosing, pk=pk, restaurant_id=rid)
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, "A reason is required to reopen a closed day (FR-144).")
        return redirect("closing:closing_list")
    closing.status = DailyClosing.Status.REOPENED
    closing.reopened_by = request.user
    closing.reopen_reason = reason
    closing.reopened_at = timezone.now()
    closing.save(update_fields=["status", "reopened_by", "reopen_reason", "reopened_at"])
    from audit_logs.services import log
    log(
        actor=request.user, action="DAY_REOPEN", entity="daily_closing",
        entity_id=closing.pk, after={"reason": reason}, request=request,
    )
    messages.warning(request, f"Day {closing.business_date} reopened — it must be re-closed this week.")
    return redirect("closing:closing_list")
