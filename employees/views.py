from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import AttendanceForm, EmployeeForm
from .models import Attendance, Employee

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .serializers import AttendanceSerializer, EmployeeSerializer

from menu.views import TenantAwareViewSet


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


# ── Employees (FR-120, FR-121) ───────────────────────────────────────


@user_passes_test(_is_manager_or_above)
def employee_list(request):
    rid = _restaurant_id(request.user)
    employees = Employee.objects.filter(restaurant_id=rid, is_deleted=False)
    q = request.GET.get("q", "").strip()
    if q:
        employees = employees.filter(full_name__icontains=q)
    return render(request, "employees/employee_list.html", {"employees": employees, "q": q})


@user_passes_test(_is_manager_or_above)
def employee_create(request):
    rid = _restaurant_id(request.user)
    form = EmployeeForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        employee = form.save(commit=False)
        employee.restaurant_id = rid
        employee.save()
        messages.success(request, f"Employee \"{employee.full_name}\" created.")
        return redirect("employees:employee_list")
    return render(request, "employees/employee_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def employee_edit(request, pk):
    rid = _restaurant_id(request.user)
    employee = get_object_or_404(Employee, pk=pk, restaurant_id=rid, is_deleted=False)
    form = EmployeeForm(request.POST or None, instance=employee, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Employee \"{employee.full_name}\" updated.")
        return redirect("employees:employee_list")
    return render(request, "employees/employee_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def employee_delete(request, pk):
    rid = _restaurant_id(request.user)
    employee = get_object_or_404(Employee, pk=pk, restaurant_id=rid, is_deleted=False)
    employee.soft_delete()
    messages.success(request, f"Employee \"{employee.full_name}\" deactivated.")
    return redirect("employees:employee_list")


# ── Attendance (FR-122, FR-123) ──────────────────────────────────────


@login_required
def attendance_list(request):
    rid = _restaurant_id(request.user)
    # Own record for non-managers; full list for managers.
    if not _is_manager_or_above(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if employee is None:
            return render(request, "employees/attendance_list.html", {"records": Attendance.objects.none(), "own_only": True})
        records = Attendance.objects.filter(employee=employee)
    else:
        records = Attendance.objects.filter(restaurant_id=rid).select_related("employee")
    month = request.GET.get("month", "")
    if month:
        records = records.filter(work_date__startswith=month)
    return render(request, "employees/attendance_list.html", {"records": records, "month": month})


@login_required
@require_POST
def attendance_clock(request):
    """FR-122: clock in/out for the user's linked employee profile."""
    rid = _restaurant_id(request.user)
    employee = getattr(request.user, "employee_profile", None)
    if employee is None:
        messages.error(request, "Your account is not linked to an employee record.")
        return redirect("employees:attendance_list")
    today = timezone.localdate()
    record, created = Attendance.objects.get_or_create(
        restaurant_id=rid, employee=employee, work_date=today,
    )
    if request.POST.get("action") == "out":
        if record.clock_in is None:
            messages.error(request, "You have not clocked in today.")
        elif record.clock_out is None:
            record.clock_out = timezone.now()
            record.save(update_fields=["clock_out"])
            messages.success(request, f"Clocked out at {record.clock_out:%H:%M}. Hours: {record.hours}.")
        else:
            messages.error(request, "You are already clocked out.")
    else:
        if record.clock_in is None:
            record.clock_in = timezone.now()
            record.save(update_fields=["clock_in"])
            messages.success(request, f"Clocked in at {record.clock_in:%H:%M}.")
        else:
            messages.error(request, "You already clocked in today.")
    return redirect("employees:attendance_list")


@user_passes_test(_is_manager_or_above)
def attendance_edit(request, pk):
    """FR-122: Owner/Manager edits are audit-logged."""
    rid = _restaurant_id(request.user)
    record = get_object_or_404(Attendance, pk=pk, restaurant_id=rid)
    form = AttendanceForm(request.POST or None, instance=record, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        before = {"clock_in": str(record.clock_in), "clock_out": str(record.clock_out)}
        form.save()
        from audit_logs.services import log
        record.refresh_from_db()
        log(
            actor=request.user, action="UPDATE", entity="attendance", entity_id=record.pk,
            before=before,
            after={"clock_in": str(record.clock_in), "clock_out": str(record.clock_out)},
            request=request,
        )
        messages.success(request, "Attendance record updated (audit-logged).")
        return redirect("employees:attendance_list")
    return render(request, "employees/attendance_form.html", {"form": form, "record": record})


#New Code
class EmployeeViewSet(TenantAwareViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        # Exclude soft-deleted employees by default
        return Employee.objects.filter(
            restaurant_id=self.get_restaurant_id(),
            is_deleted=False,
        ).select_related("user")

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.OWNER, User.Role.MANAGER}:
            raise PermissionDenied("Only Owners and Managers can create employees.")

        serializer.save(restaurant_id=self.get_restaurant_id())

    def perform_update(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.OWNER, User.Role.MANAGER}:
            raise PermissionDenied("Only Owners and Managers can update employee records.")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in {User.Role.OWNER, User.Role.MANAGER}:
            raise PermissionDenied("Only Owners and Managers can delete employees.")

        # Soft delete execution
        instance.soft_delete()


class AttendanceViewSet(TenantAwareViewSet):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        rid = self.get_restaurant_id()
        queryset = Attendance.objects.filter(
            restaurant_id=rid
        ).select_related("employee")

        # Optional query parameters filtering
        employee_id = self.request.query_params.get("employee")
        work_date = self.request.query_params.get("date")

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if work_date:
            queryset = queryset.filter(work_date=work_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(restaurant_id=self.get_restaurant_id())

    @action(detail=False, methods=["post"], url_path="clock-in")
    def clock_in(self, request):
        """FR-122: Clock-in action for employee for today's business date."""
        rid = self.get_restaurant_id()
        employee_id = request.data.get("employee_id")

        if not employee_id:
            raise ValidationError({"employee_id": "Employee ID is required."})

        employee = Employee.objects.filter(
            id=employee_id, restaurant_id=rid, is_deleted=False
        ).first()

        if not employee:
            return Response(
                {"detail": "Active employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.localdate()
        attendance, created = Attendance.objects.get_or_create(
            restaurant_id=rid,
            employee=employee,
            work_date=today,
        )

        if attendance.clock_in and not created:
            return Response(
                {"detail": f"Employee already clocked in today at {attendance.clock_in}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendance.clock_in = timezone.now()
        attendance.save()

        return Response(AttendanceSerializer(attendance, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="clock-out")
    def clock_out(self, request):
        """FR-122: Clock-out action for employee for today's business date."""
        rid = self.get_restaurant_id()
        employee_id = request.data.get("employee_id")

        if not employee_id:
            raise ValidationError({"employee_id": "Employee ID is required."})

        today = timezone.localdate()
        attendance = Attendance.objects.filter(
            restaurant_id=rid,
            employee_id=employee_id,
            work_date=today,
        ).first()

        if not attendance or not attendance.clock_in:
            return Response(
                {"detail": "No active clock-in found for today."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attendance.clock_out:
            return Response(
                {"detail": "Employee has already clocked out for today."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendance.clock_out = timezone.now()
        attendance.save()

        return Response(AttendanceSerializer(attendance, context={"request": request}).data)