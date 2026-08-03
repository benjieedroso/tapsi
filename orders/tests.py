from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User
from closing.models import DailyClosing
from inventory.models import Ingredient, InventoryTransaction
from menu.models import AddOn, Category, MenuItem
from recipes.models import Recipe, RecipeIngredient

from .models import DiningTable, Order, OrderItem, OrderItemAddon, Payment
from .services import (
    cancel_order, deduct_recipe_stock, record_payment, refund_payment, settle_order,
)
from .forms import OrderForm

TODAY = timezone.localdate()


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class OrderBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.category = Category.objects.create(restaurant_id=self.rid, name="Rice Meals")
        self.menu_item = MenuItem.objects.create(
            restaurant_id=self.rid, category=self.category,
            name="Chicken Adobo", price=Decimal("100"),
        )
        self.addon = AddOn.objects.create(
            restaurant_id=self.rid, name="Extra Rice", price=Decimal("15"),
        )
        self.rice = Ingredient.objects.create(
            restaurant_id=self.rid, name="Rice", unit_of_measure="kg",
            average_unit_cost=Decimal("50"), minimum_stock=Decimal("1"),
        )
        self.chicken = Ingredient.objects.create(
            restaurant_id=self.rid, name="Chicken", unit_of_measure="kg",
            average_unit_cost=Decimal("180"), minimum_stock=Decimal("1"),
        )
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Adobo Recipe",
        )
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.rice, quantity=Decimal("0.2"))
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.chicken, quantity=Decimal("0.3"))
        self.table = DiningTable.objects.create(restaurant_id=self.rid, name="T1", seating_capacity=4)

    def _make_order(self, order_type=Order.Type.DINE_IN, table=None):
        order = Order.objects.create(
            restaurant_id=self.rid,
            order_type=order_type,
            table=table or self.table,
            created_by=self.owner,
        )
        order.order_number = f"#{Order.objects.filter(restaurant_id=self.rid).count():04d}"
        order.save(update_fields=["order_number"])
        return order

    def _add_item(self, order, item=None, qty=1, addons=()):
        menu_item = item or self.menu_item
        line = OrderItem.objects.create(
            order=order, menu_item=menu_item,
            item_name=menu_item.name, unit_price=menu_item.price, quantity=qty,
        )
        for addon in addons:
            OrderItemAddon.objects.create(
                order_item=line, addon=addon, addon_name=addon.name, price=addon.price,
            )
        order.recompute_totals()
        return line

    def _stock(self, ingredient, qty):
        InventoryTransaction.objects.create(
            ingredient=ingredient,
            transaction_type=InventoryTransaction.Type.PURCHASE,
            quantity=qty, unit_cost=ingredient.average_unit_cost or Decimal("50"),
        )

    def _pay_in_full(self, order, method=Payment.Method.CASH):
        return record_payment(
            order, method, order.total, self.owner,
            reference_no="REF-1" if method != Payment.Method.CASH else "",
        )


class OrderNumberTests(OrderBase):
    def test_sequential_per_restaurant_and_day(self):
        """FR-081: #0001, #0002 per restaurant/day."""
        o1 = self._make_order()
        o2 = self._make_order()
        self.assertEqual(o1.order_number, "#0001")
        self.assertEqual(o2.order_number, "#0002")


class OrderFormTests(OrderBase):
    def test_dine_in_requires_table(self):
        form = OrderForm(data={"order_type": Order.Type.DINE_IN}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("table", form.errors)

    def test_delivery_requires_customer(self):
        form = OrderForm(data={"order_type": Order.Type.DELIVERY}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("customer_name", form.errors)
        self.assertIn("customer_phone", form.errors)
        self.assertIn("customer_address", form.errors)

    def test_takeout_valid_without_table(self):
        form = OrderForm(data={"order_type": Order.Type.TAKE_OUT}, restaurant_id=self.rid)
        self.assertTrue(form.is_valid(), form.errors)


class OrderMoneyTests(OrderBase):
    def test_vat_math_on_plain_order(self):
        """BR-011/FR-103: subtotal 100 + 15 addon = 115; VAT 12% of 115."""
        order = self._make_order()
        self._add_item(order, addons=[self.addon])
        self.assertEqual(order.subtotal, Decimal("115.00"))
        self.assertEqual(order.vatable_sales, Decimal("115.00"))
        self.assertEqual(order.vat_amount, Decimal("13.80"))
        self.assertEqual(order.total, Decimal("115.00"))

    def test_senior_discount_is_20pct_and_vat_exempt(self):
        """BR-009: Senior/PWD discount is VAT-exempt (RA 9994)."""
        order = self._make_order()
        self._add_item(order, addons=[self.addon])
        order.apply_discount(Order.DiscountType.SENIOR, discount_ref="SEN-1234", user=self.owner)
        self.assertEqual(order.discount_amount, Decimal("23.00"))
        self.assertEqual(order.vat_exempt_sales, Decimal("23.00"))
        self.assertEqual(order.vatable_sales, Decimal("92.00"))
        self.assertEqual(order.vat_amount, Decimal("11.04"))
        self.assertEqual(order.total, Decimal("92.00"))

    def test_senior_requires_id_number(self):
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError):
            order.apply_discount(Order.DiscountType.PWD, discount_ref="", user=self.owner)

    def test_manual_discount_above_10_requires_approval(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        order = self._make_order()
        self._add_item(order)
        order.apply_discount(Order.DiscountType.MANUAL, pct=15, user=cashier)
        self.assertTrue(order.discount_needs_approval)
        self.assertIsNone(order.discount_approved_by)

    def test_manager_manual_discount_auto_approved(self):
        manager = User.objects.create_user(
            email="manager@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        order = self._make_order()
        self._add_item(order)
        order.apply_discount(Order.DiscountType.MANUAL, pct=15, user=manager)
        self.assertFalse(order.discount_needs_approval)
        self.assertEqual(order.discount_approved_by, manager)

    def test_discount_only_on_pending_orders(self):
        order = self._make_order()
        self._add_item(order)
        order.transition_to(Order.Status.PREPARING, self.owner)
        with self.assertRaises(ValidationError):
            order.apply_discount(Order.DiscountType.SENIOR, discount_ref="SEN-1", user=self.owner)


class OrderStatusTests(OrderBase):
    def test_valid_transitions(self):
        order = self._make_order()
        order.transition_to(Order.Status.PREPARING, self.owner)
        self.assertEqual(order.status, Order.Status.PREPARING)
        order.transition_to(Order.Status.READY, self.owner)
        order.transition_to(Order.Status.COMPLETED, self.owner)
        self.assertEqual(order.status, Order.Status.COMPLETED)

    def test_invalid_transition_rejected(self):
        order = self._make_order()
        order.transition_to(Order.Status.PREPARING, self.owner)
        with self.assertRaises(ValidationError):
            order.transition_to(Order.Status.COMPLETED, self.owner)

    def test_status_history_recorded(self):
        order = self._make_order()
        order.transition_to(Order.Status.READY, self.owner)
        self.assertEqual(order.status_history.count(), 1)
        history = order.status_history.first()
        self.assertEqual(history.old_status, Order.Status.PENDING)
        self.assertEqual(history.new_status, Order.Status.READY)


class PaymentTests(OrderBase):
    def test_cash_payment_with_change(self):
        order = self._make_order()
        self._add_item(order)  # total 100
        payment = record_payment(order, Payment.Method.CASH, Decimal("100"), self.owner, tendered=Decimal("500"))
        self.assertEqual(payment.change_given, Decimal("400.00"))
        self.assertTrue(order.is_settled)

    def test_non_cash_requires_reference(self):
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError):
            record_payment(order, Payment.Method.GCASH, Decimal("100"), self.owner)

    def test_non_cash_cannot_overpay(self):
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError):
            record_payment(order, Payment.Method.CARD, Decimal("150"), self.owner, reference_no="X")

    def test_cash_overpay_allowed(self):
        order = self._make_order()
        self._add_item(order)
        payment = record_payment(order, Payment.Method.CASH, Decimal("150"), self.owner)
        self.assertEqual(payment.amount, Decimal("150.00"))

    def test_payments_are_immutable(self):
        order = self._make_order()
        self._add_item(order)
        payment = record_payment(order, Payment.Method.CASH, Decimal("100"), self.owner)
        with self.assertRaises(ValidationError):
            payment.delete()

    def test_refund_requires_reason_and_links_original(self):
        """FR-105: negative payment with refund_of link."""
        order = self._make_order()
        self._add_item(order)
        payment = record_payment(order, Payment.Method.CASH, Decimal("100"), self.owner)
        with self.assertRaises(ValidationError):
            refund_payment(payment, self.owner, "")
        refund = refund_payment(payment, self.owner, "Wrong item")
        self.assertEqual(refund.amount, Decimal("-100.00"))
        self.assertEqual(refund.refund_of, payment)
        self.assertEqual(order.refunded_amount, Decimal("100.00"))


class SettlementTests(OrderBase):
    def test_complete_requires_full_payment(self):
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError) as ctx:
            settle_order(order, self.owner)
        self.assertIn("not fully paid", str(ctx.exception))

    def test_complete_requires_approved_discount(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        order.apply_discount(Order.DiscountType.MANUAL, pct=15, user=cashier)
        self.assertTrue(order.discount_needs_approval)
        self._pay_in_full(order)
        with self.assertRaises(ValidationError) as ctx:
            settle_order(order, self.owner)
        self.assertIn("approval", str(ctx.exception))
        order.approve_discount(self.owner)
        settle_order(order, self.owner)
        self.assertEqual(order.status, Order.Status.COMPLETED)

    def test_complete_deducts_recipe_stock(self):
        """FR-072/FR-073/BR-001: completion consumes recipe ingredients."""
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order, qty=2)  # 2× rice 0.2kg + 2× chicken 0.3kg
        self._pay_in_full(order)
        settle_order(order, self.owner)
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.rice.refresh_from_db()
        self.chicken.refresh_from_db()
        self.assertEqual(self.rice.current_stock, Decimal("4.6"))
        self.assertEqual(self.chicken.current_stock, Decimal("4.4"))
        self.assertEqual(
            InventoryTransaction.objects.filter(transaction_type=InventoryTransaction.Type.CONSUMPTION).count(),
            2,
        )

    def test_completion_frees_table_to_cleaning(self):
        """FR-091: last order on a table leaves it CLEANING."""
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        self._pay_in_full(order)
        settle_order(order, self.owner)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, DiningTable.Status.CLEANING)

    def test_cancel_frees_table_to_cleaning(self):
        """FR-091: cancelling the only order on a table frees it."""
        order = self._make_order()
        self._add_item(order)
        cancel_order(order, self.owner, "Customer left")
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, DiningTable.Status.CLEANING)
        self.assertEqual(self.table.open_orders.count(), 0)

    def test_complete_blocked_by_stock_shortage(self):
        """FR-073/BR-001: lists all shortages, nothing deducted."""
        self._stock(self.rice, 0.1)  # need 0.2
        self._stock(self.chicken, 0.2)  # need 0.3
        order = self._make_order()
        self._add_item(order)
        self._pay_in_full(order)
        with self.assertRaises(ValidationError) as ctx:
            settle_order(order, self.owner)
        self.assertIn("insufficient stock", str(ctx.exception))
        self.assertIn("Rice", str(ctx.exception))
        self.assertIn("Chicken", str(ctx.exception))
        self.assertEqual(InventoryTransaction.objects.filter(
            transaction_type=InventoryTransaction.Type.CONSUMPTION).count(), 0)
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_complete_assigns_sequential_receipt_numbers(self):
        """FR-103: receipt serial 1, 2 per restaurant."""
        for _ in range(2):
            self._stock(self.rice, 5)
            self._stock(self.chicken, 5)
            order = self._make_order()
            self._add_item(order)
            self._pay_in_full(order)
            settle_order(order, self.owner)
        orders = Order.objects.filter(restaurant_id=self.rid).order_by("receipt_no")
        self.assertEqual(list(orders.values_list("receipt_no", flat=True)), [1, 2])

    def test_completed_order_cannot_be_cancelled(self):
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        self._pay_in_full(order)
        settle_order(order, self.owner)
        with self.assertRaises(ValidationError):
            cancel_order(order, self.owner, "oops")


class CancellationTests(OrderBase):
    def test_cancel_requires_reason(self):
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError):
            cancel_order(order, self.owner, "")

    def test_cancelling_completed_order_requires_refund_flow(self):
        """FR-105/BR-005: completed orders are immutable."""
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        self._pay_in_full(order)
        settle_order(order, self.owner)
        with self.assertRaises(ValidationError) as ctx:
            cancel_order(order, self.owner, "oops")
        self.assertIn("immutable", str(ctx.exception))

    def test_cancel_restores_consumed_stock(self):
        """FR-086/BR-003: compensating ADJUSTMENT entries reverse consumption."""
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        # Simulate consumption already posted for this order.
        deduct_recipe_stock(order, self.owner)
        self.rice.refresh_from_db()
        self.assertEqual(self.rice.current_stock, Decimal("4.8"))
        restored = cancel_order(order, self.owner, "Customer changed mind")
        self.assertEqual(restored, 2)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.cancel_reason, "Customer changed mind")
        self.rice.refresh_from_db()
        self.chicken.refresh_from_db()
        self.assertEqual(self.rice.current_stock, Decimal("5"))
        self.assertEqual(self.chicken.current_stock, Decimal("5"))


class DayLockTests(OrderBase):
    def _close_day(self):
        DailyClosing.objects.create(
            restaurant_id=self.rid, business_date=TODAY, status=DailyClosing.Status.CLOSED,
            closed_by=self.owner,
        )

    def test_payment_rejected_on_closed_day(self):
        """BR-008: closed days reject new payments."""
        self._close_day()
        order = self._make_order()
        self._add_item(order)
        with self.assertRaises(ValidationError) as ctx:
            record_payment(order, Payment.Method.CASH, Decimal("100"), self.owner)
        self.assertIn("closed", str(ctx.exception))

    def test_order_creation_blocked_on_closed_day(self):
        self._close_day()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("orders:order_create"), {
            "order_type": Order.Type.TAKE_OUT,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(restaurant_id=self.rid).count(), 0)

    def test_cancel_blocked_on_closed_day(self):
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = self._make_order()
        self._add_item(order)
        deduct_recipe_stock(order, self.owner)
        self._close_day()
        with self.assertRaises(ValidationError):
            cancel_order(order, self.owner, "test")


class KitchenTests(OrderBase):
    def test_kitchen_advance_flow(self):
        """FR-088: PENDING → PREPARING → READY by kitchen role."""
        kitchen = User.objects.create_user(
            email="kitchen@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.KITCHEN,
        )
        order = self._make_order()
        self._add_item(order)
        self.client.force_login(kitchen)
        self.client.post(reverse("orders:kitchen_advance", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
        self.client.post(reverse("orders:kitchen_advance", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)

    def test_cashier_cannot_advance_kitchen_status(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        order = self._make_order()
        self._add_item(order)
        self.client.force_login(cashier)
        response = self.client.post(reverse("orders:kitchen_advance", args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)


class OrderViewTests(OrderBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def test_create_order_via_view_sets_number_and_occupies_table(self):
        response = self.client.post(reverse("orders:order_create"), {
            "order_type": Order.Type.DINE_IN,
            "table": self.table.pk,
        })
        order = Order.objects.get(restaurant_id=self.rid)
        self.assertRedirects(response, reverse("orders:order_detail", args=[order.pk]))
        self.assertEqual(order.order_number, "#0001")
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, DiningTable.Status.OCCUPIED)

    def test_add_item_with_addon_snapshots(self):
        """FR-082: name/price snapshots at sale time."""
        order = self._make_order()
        response = self.client.post(reverse("orders:order_item_add", args=[order.pk]), {
            "menu_item": self.menu_item.pk,
            "quantity": "2",
            "addons": [self.addon.pk],
            "notes": "no onions",
        })
        self.assertRedirects(response, reverse("orders:order_detail", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.item_name, "Chicken Adobo")
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.addons.first().addon_name, "Extra Rice")
        self.assertEqual(order.subtotal, Decimal("230.00"))

    def test_item_add_blocked_after_pending(self):
        order = self._make_order()
        self._add_item(order)
        order.transition_to(Order.Status.PREPARING, self.owner)
        response = self.client.post(reverse("orders:order_item_add", args=[order.pk]), {
            "menu_item": self.menu_item.pk, "quantity": "1",
        })
        self.assertRedirects(response, reverse("orders:order_detail", args=[order.pk]))
        self.assertEqual(order.items.count(), 1)
