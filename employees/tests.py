from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User
from audit_logs.models import AuditLog

from .models import Attendance, Employee


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class EmployeeBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.client.force_login(self.owner)
        self.employee = Employee.objects.create(
            restaurant_id=self.rid, full_name="Juan Dela Cruz",
            position="Waiter", daily_rate=500, monthly_salary=12000,
        )

    def _post(self, url_name, pk=None, **data):
        url = reverse(url_name, args=[pk]) if pk else reverse(url_name)
        return self.client.post(url, data)


class EmployeeViewTests(EmployeeBase):
    def test_create_employee(self):
        response = self._post("employees:employee_create",
                              full_name="Maria Santos", position="Cashier",
                              employment_status="ACTIVE",
                              daily_rate="500", monthly_salary="13000")
        self.assertRedirects(response, reverse("employees:employee_list"))
        employee = Employee.objects.get(full_name="Maria Santos")
        self.assertEqual(employee.restaurant_id, self.rid)

    def test_edit_employee(self):
        response = self._post("employees:employee_edit", self.employee.pk,
                              full_name="Juan Dela Cruz Jr.", position="Head Waiter",
                              employment_status="ACTIVE",
                              daily_rate="600", monthly_salary="14000")
        self.assertRedirects(response, reverse("employees:employee_list"))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, "Head Waiter")

    def test_delete_soft_deletes(self):
        response = self._post("employees:employee_delete", self.employee.pk)
        self.assertRedirects(response, reverse("employees:employee_list"))
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.is_deleted)

    def test_cashier_cannot_manage_employees(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse("employees:employee_list"))
        self.assertEqual(response.status_code, 302)


class AttendanceViewTests(EmployeeBase):
    def setUp(self):
        super().setUp()
        self.employee.user = self.owner
        self.employee.save()

    def test_clock_in_and_out(self):
        response = self._post("employees:attendance_clock", action="in")
        self.assertRedirects(response, reverse("employees:attendance_list"))
        record = Attendance.objects.get(employee=self.employee)
        self.assertIsNotNone(record.clock_in)
        response = self._post("employees:attendance_clock", action="out")
        record.refresh_from_db()
        self.assertIsNotNone(record.clock_out)

    def test_clock_in_once_per_day(self):
        self._post("employees:attendance_clock", action="in")
        self._post("employees:attendance_clock", action="in")
        self.assertEqual(Attendance.objects.filter(employee=self.employee).count(), 1)

    def test_hours_property(self):
        now = timezone.now()
        record = Attendance.objects.create(
            restaurant_id=self.rid, employee=self.employee, work_date=timezone.localdate(),
            clock_in=now - timezone.timedelta(hours=8),
            clock_out=now,
        )
        self.assertEqual(record.hours, 8.0)

    def test_attendance_edit_audit_logged(self):
        record = Attendance.objects.create(
            restaurant_id=self.rid, employee=self.employee, work_date=timezone.localdate(),
            clock_in=timezone.now() - timezone.timedelta(hours=8),
            clock_out=timezone.now() - timezone.timedelta(hours=1),
        )
        response = self._post("employees:attendance_edit", record.pk,
                              employee=self.employee.pk,
                              work_date=record.work_date.isoformat(),
                              clock_in=record.clock_in.isoformat(),
                              clock_out=record.clock_out.isoformat())
        self.assertRedirects(response, reverse("employees:attendance_list"))
        self.assertTrue(AuditLog.objects.filter(
            action="UPDATE", entity="attendance", entity_id=record.pk).exists())

    def test_own_record_only_for_cashier(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        cashier_emp = Employee.objects.create(
            restaurant_id=self.rid, full_name="Cashier Emp", user=cashier,
        )
        Attendance.objects.create(
            restaurant_id=self.rid, employee=self.employee, work_date=timezone.localdate(),
            clock_in=timezone.now() - timezone.timedelta(hours=8), clock_out=timezone.now(),
        )
        Attendance.objects.create(
            restaurant_id=self.rid, employee=cashier_emp, work_date=timezone.localdate(),
            clock_in=timezone.now() - timezone.timedelta(hours=7), clock_out=timezone.now(),
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse("employees:attendance_list"))
        self.assertContains(response, "Cashier Emp")
        self.assertNotContains(response, "Juan Dela Cruz")
