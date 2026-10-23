from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User

from .forms import ExpenseForm
from .models import Expense
from .serializers import ExpenseSerializer

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from menu.views import TenantAwareViewSet

APPROVAL_THRESHOLD = 5000  # FR-111: default ₱5,000

#Legacy
def _is_staff(user):
    return user.is_authenticated and user.role in {
        User.Role.OWNER, User.Role.MANAGER, User.Role.CASHIER,
    }


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


def _day_open(rid, expense_date):
    """BR-008: closed days reject new expenses (FR-113)."""
    from closing.models import DailyClosing

    return not DailyClosing.objects.filter(
        restaurant_id=rid,
        business_date=expense_date,
        status=DailyClosing.Status.CLOSED,
    ).exists()


@user_passes_test(_is_staff)
def expense_list(request):
    rid = _restaurant_id(request.user)
    expenses = Expense.objects.filter(restaurant_id=rid).select_related("created_by")
    category = request.GET.get("category", "")
    status = request.GET.get("status", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    if category:
        expenses = expenses.filter(category=category)
    if status:
        expenses = expenses.filter(status=status)
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)
    return render(request, "expenses/expense_list.html", {
        "expenses": expenses,
        "category": category,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "categories": Expense.Category.choices,
    })


@user_passes_test(_is_staff)
def expense_create(request):
    """FR-110: Cashier may create. FR-111: over-threshold expenses by a
    Cashier require Owner/Manager approval."""
    rid = _restaurant_id(request.user)
    form = ExpenseForm(request.POST or None, request.FILES or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        if not _day_open(rid, form.cleaned_data["expense_date"]):
            messages.error(request, "This business day is closed — expenses cannot be recorded (FR-113).")
            return render(request, "expenses/expense_form.html", {"form": form, "action": "Create"})
        expense = form.save(commit=False)
        expense.restaurant_id = rid
        expense.created_by = request.user
        is_manager = request.user.role in {User.Role.OWNER, User.Role.MANAGER}
        if not is_manager and expense.amount > APPROVAL_THRESHOLD:
            expense.status = Expense.Status.PENDING
        expense.save()
        if expense.status == Expense.Status.PENDING:
            messages.warning(request, "Expense saved and is pending Owner/Manager approval (FR-111).")
        else:
            messages.success(request, "Expense recorded.")
        return redirect("expenses:expense_list")
    return render(request, "expenses/expense_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def expense_edit(request, pk):
    """FR-113: closed-day expenses are not editable; corrections are new
    entries on an open day."""
    rid = _restaurant_id(request.user)
    expense = get_object_or_404(Expense, pk=pk, restaurant_id=rid)
    if not _day_open(rid, expense.expense_date):
        messages.error(request, "This business day is closed — expenses are locked (FR-113).")
        return redirect("expenses:expense_list")
    form = ExpenseForm(request.POST or None, request.FILES or None, instance=expense, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Expense updated.")
        return redirect("expenses:expense_list")
    return render(request, "expenses/expense_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def expense_delete(request, pk):
    rid = _restaurant_id(request.user)
    expense = get_object_or_404(Expense, pk=pk, restaurant_id=rid)
    if not _day_open(rid, expense.expense_date):
        messages.error(request, "This business day is closed — expenses are locked (FR-113).")
        return redirect("expenses:expense_list")
    expense.delete()
    messages.success(request, "Expense deleted.")
    return redirect("expenses:expense_list")


@user_passes_test(_is_manager_or_above)
@require_POST
def expense_approve(request, pk):
    """FR-111: approve an over-threshold Cashier expense."""
    rid = _restaurant_id(request.user)
    expense = get_object_or_404(Expense, pk=pk, restaurant_id=rid)
    expense.status = Expense.Status.APPROVED
    expense.approved_by = request.user
    expense.save(update_fields=["status", "approved_by"])
    messages.success(request, f"Expense approved — it now appears in reports.")
    return redirect("expenses:expense_list")

#New Code:
class ExpenseViewSet(TenantAwareViewSet):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        queryset = Expense.objects.filter(
            restaurant_id=self.get_restaurant_id()
        ).select_related("created_by", "approved_by").order_by("-expense_date", "-created_at")

        # Optional query param filters for category, status & date range
        category_param = self.request.query_params.get("category")
        status_param = self.request.query_params.get("status")
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")

        if category_param:
            queryset = queryset.filter(category=category_param)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if date_from:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(expense_date__lte=date_to)

        return queryset

    def list(self, request, *args, **kwargs):
        """Returns expenses list combined with dropdown options for the frontend UI."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "expenses": serializer.data,
            "categories": Expense.Category.choices,
            "statuses": Expense.Status.choices,
        })

    def perform_create(self, serializer):
        # Automatically attach restaurant_id and created_by user from request
        serializer.save(
            restaurant_id=self.get_restaurant_id(),
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """FR-110..FR-113 Approval Workflow Action"""
        expense = self.get_object()

        if expense.status == Expense.Status.APPROVED:
            return Response(
                {"detail": "Expense is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expense.status = Expense.Status.APPROVED
        expense.approved_by = request.user
        expense.save(update_fields=["status", "approved_by", "updated_at"])

        return Response(ExpenseSerializer(expense).data)

    @action(detail=False, methods=["get"], url_path="categories")
    def categories(self, request):
        """Returns available expense categories for dropdown selection."""
        category_choices = [
            {"value": choice[0], "label": choice[1]} 
            for choice in Expense.Category.choices
        ]
        return Response(category_choices)