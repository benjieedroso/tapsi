from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Restaurant, User
from closing.models import DailyClosing
from django.utils import timezone

from .models import Expense

TODAY = timezone.localdate()


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class ExpenseBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )

    def _expense(self, amount="200", **kwargs):
        data = {"category": Expense.Category.SUPPLIES, "amount": amount,
                "expense_date": TODAY.isoformat(), "payment_method": "CASH"}
        data.update(kwargs)
        return data


class ExpenseModelTests(ExpenseBase):
    def test_approval_status_pending_by_default_for_cashier_flow(self):
        expense = Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.SUPPLIES,
            amount=Decimal("200"), expense_date=TODAY, created_by=self.cashier,
            status=Expense.Status.PENDING,
        )
        self.assertEqual(expense.status, Expense.Status.PENDING)


class ExpenseViewTests(ExpenseBase):
    def test_cashier_under_threshold_auto_approved(self):
        self.client.force_login(self.cashier)
        response = self.client.post(reverse("expenses:expense_create"), self._expense())
        self.assertRedirects(response, reverse("expenses:expense_list"))
        expense = Expense.objects.get(restaurant_id=self.rid)
        self.assertEqual(expense.status, Expense.Status.APPROVED)

    def test_cashier_over_threshold_pending_approval(self):
        """FR-111: cashier expense above ₱5,000 requires approval."""
        self.client.force_login(self.cashier)
        response = self.client.post(reverse("expenses:expense_create"), self._expense(amount="6000"))
        expense = Expense.objects.get(restaurant_id=self.rid)
        self.assertEqual(expense.status, Expense.Status.PENDING)

    def test_manager_expense_never_pending(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("expenses:expense_create"), self._expense(amount="6000"))
        expense = Expense.objects.get(restaurant_id=self.rid)
        self.assertEqual(expense.status, Expense.Status.APPROVED)

    def test_approve_pending_expense(self):
        expense = Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.WATER,
            amount=Decimal("6000"), expense_date=TODAY, created_by=self.cashier,
            status=Expense.Status.PENDING,
        )
        self.client.force_login(self.owner)
        response = self.client.post(reverse("expenses:expense_approve", args=[expense.pk]))
        self.assertRedirects(response, reverse("expenses:expense_list"))
        expense.refresh_from_db()
        self.assertEqual(expense.status, Expense.Status.APPROVED)
        self.assertEqual(expense.approved_by, self.owner)

    def test_cashier_cannot_approve(self):
        expense = Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.WATER,
            amount=Decimal("6000"), expense_date=TODAY, created_by=self.cashier,
            status=Expense.Status.PENDING,
        )
        self.client.force_login(self.cashier)
        response = self.client.post(reverse("expenses:expense_approve", args=[expense.pk]))
        self.assertEqual(response.status_code, 302)
        expense.refresh_from_db()
        self.assertEqual(expense.status, Expense.Status.PENDING)

    def test_create_blocked_on_closed_day(self):
        """FR-113/BR-008: closed day rejects new expenses."""
        DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY,
            status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        self.client.force_login(self.cashier)
        response = self.client.post(reverse("expenses:expense_create"), self._expense())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.filter(restaurant_id=self.rid).count(), 0)

    def test_edit_and_delete_blocked_on_closed_day(self):
        expense = Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.SUPPLIES,
            amount=Decimal("200"), expense_date=TODAY, created_by=self.owner,
        )
        DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY,
            status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse("expenses:expense_edit", args=[expense.pk]))
        self.assertRedirects(response, reverse("expenses:expense_list"))
        response = self.client.post(reverse("expenses:expense_delete", args=[expense.pk]))
        self.assertRedirects(response, reverse("expenses:expense_list"))
        self.assertTrue(Expense.objects.filter(pk=expense.pk).exists())

    def test_kitchen_cannot_access_expenses(self):
        kitchen = User.objects.create_user(
            email="kitchen@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.KITCHEN,
        )
        self.client.force_login(kitchen)
        response = self.client.get(reverse("expenses:expense_list"))
        self.assertEqual(response.status_code, 302)
