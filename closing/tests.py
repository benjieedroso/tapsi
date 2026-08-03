from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User
from closing.models import DailyClosing
from expenses.models import Expense
from orders.models import Order, Payment
from orders.services import record_payment

TODAY = timezone.localdate()


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class ClosingBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.manager = User.objects.create_user(
            email="manager@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        self.client.force_login(self.owner)


class DailyClosingModelTests(ClosingBase):
    def test_is_locked_detects_closed_days(self):
        self.assertFalse(DailyClosing.is_locked(self.rid, TODAY))
        DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY,
            status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        self.assertTrue(DailyClosing.is_locked(self.rid, TODAY))

    def test_expected_cash_flow(self):
        """FR-140: expected = opening float + cash sales − cash refunds − cash expenses."""
        DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY - timezone.timedelta(days=1),
            opening_float=1000, expected_cash=1000, counted_cash=2500,
            variance=0, status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        order = Order.objects.create(
            restaurant_id=self.rid, order_type=Order.Type.TAKE_OUT,
            created_by=self.owner, total=Decimal("1000"),
        )
        order.order_number = "#0001"
        order.save(update_fields=["order_number"])
        record_payment(order, Payment.Method.CASH, Decimal("500"), self.owner)
        record_payment(order, Payment.Method.GCASH, Decimal("500"), self.owner, reference_no="G1")
        refund = Payment.objects.get(method=Payment.Method.GCASH)
        from orders.services import refund_payment
        refund_payment(refund, self.owner, "test refund")
        Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.WATER,
            amount=Decimal("150"), expense_date=TODAY, status=Expense.Status.APPROVED,
            payment_method="CASH", created_by=self.owner,
        )
        # Cash sales 500 − cash refund 0 − cash expenses 150 + float 2500
        self.assertEqual(
            DailyClosing.expected_cash_for(self.rid, TODAY), Decimal("2850.00"),
        )

    def test_reopen_flow_and_status(self):
        closing = DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY,
            opening_float=1000, expected_cash=1000, counted_cash=1000,
            variance=0, status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        response = self.client.post(reverse("closing:closing_reopen", args=[closing.pk]), {"reason": "Correction"})
        self.assertRedirects(response, reverse("closing:closing_list"))
        closing.refresh_from_db()
        self.assertEqual(closing.status, DailyClosing.Status.REOPENED)
        self.assertEqual(closing.reopened_by, self.owner)
        self.assertEqual(closing.reopen_reason, "Correction")
        self.assertFalse(DailyClosing.is_locked(self.rid, TODAY))


class ClosingViewTests(ClosingBase):
    def test_prepare_shows_open_orders_blocker(self):
        order = Order.objects.create(
            restaurant_id=self.rid, order_type=Order.Type.TAKE_OUT,
            created_by=self.owner, total=Decimal("100"),
        )
        order.order_number = "#0001"
        order.save(update_fields=["order_number"])
        response = self.client.get(reverse("closing:closing_prepare"))
        self.assertContains(response, "#0001")

    def test_complete_requires_variance_note_beyond_limit(self):
        """FR-141: variance beyond ±₱100 needs a written explanation."""
        response = self.client.post(reverse("closing:closing_complete"), {"counted_cash": "500"})
        self.assertRedirects(response, reverse("closing:closing_prepare"))
        self.assertFalse(DailyClosing.objects.filter(restaurant_id=self.rid).exists())

    def test_complete_creates_closing_and_locks_day(self):
        response = self.client.post(
            reverse("closing:closing_complete"),
            {"counted_cash": "0", "variance_note": ""},
        )
        closing = DailyClosing.objects.get(restaurant_id=self.rid)
        self.assertRedirects(response, reverse("closing:eod_report", args=[closing.pk]))
        self.assertEqual(closing.status, DailyClosing.Status.CLOSED)
        self.assertTrue(DailyClosing.is_locked(self.rid, TODAY))
        self.assertEqual(closing.counted_cash, Decimal("0"))
        self.assertEqual(closing.variance, Decimal("0"))

    def test_manager_cannot_reopen(self):
        """FR-144: only the Owner may reopen."""
        closing = DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY,
            opening_float=0, expected_cash=0, counted_cash=0,
            variance=0, status=DailyClosing.Status.CLOSED, closed_by=self.owner,
        )
        self.client.force_login(self.manager)
        response = self.client.post(reverse("closing:closing_reopen", args=[closing.pk]), {"reason": "why"})
        self.assertEqual(response.status_code, 302)
        closing.refresh_from_db()
        self.assertEqual(closing.status, DailyClosing.Status.CLOSED)
