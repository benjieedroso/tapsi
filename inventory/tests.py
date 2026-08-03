from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Restaurant, User

from .models import Ingredient, InventoryTransaction, LowStockAlert
from .forms import IngredientForm, IngredientTransactionForm


class InventoryTestBase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Testaurant")
        self.other = Restaurant.objects.create(name="Other")
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass1234",
            first_name="Own", last_name="Er",
            restaurant=self.restaurant, role=User.Role.OWNER,
        )
        self.manager = User.objects.create_user(
            email="manager@test.com", password="testpass1234",
            first_name="Man", last_name="Ager",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        self.cashier = User.objects.create_user(
            email="cashier@test.com", password="testpass1234",
            first_name="Ca", last_name="Shier",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client = Client()


def make_ingredient(restaurant_id, name="Rice", **kwargs):
    return Ingredient.objects.create(restaurant_id=restaurant_id, name=name, **kwargs)


def record(ingredient, txn_type, quantity, **kwargs):
    txn = InventoryTransaction(
        ingredient=ingredient,
        transaction_type=txn_type,
        quantity=quantity,
        **kwargs,
    )
    txn.save()
    return txn


# ── Ingredient CRUD (FR-040, FR-041) ────────────────────────────────


class IngredientCreateTests(InventoryTestBase):
    def test_owner_can_create_ingredient(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_create"), {
            "name": "Sinigang Mix",
            "unit_of_measure": "pack",
            "minimum_stock": "10",
            "average_unit_cost": "25.00",
        })
        self.assertEqual(resp.status_code, 302)
        ing = Ingredient.objects.first()
        self.assertEqual(ing.name, "Sinigang Mix")
        self.assertEqual(ing.restaurant_id, self.restaurant.pk)
        self.assertEqual(ing.minimum_stock, Decimal("10"))

    def test_ingredient_name_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_create"), {"name": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["name"])

    def test_ingredient_name_min_2_chars(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_create"), {"name": "A"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["name"])

    def test_ingredient_name_unique_per_restaurant_case_insensitive(self):
        make_ingredient(self.restaurant.pk, name="Rice")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_create"), {"name": "rice"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["name"])

    def test_soft_deleted_name_can_be_reused(self):
        ing = make_ingredient(self.restaurant.pk, name="Rice")
        ing.soft_delete()
        self.client.login(email="owner@test.com", password="testpass1234")
        resp =         self.client.post(reverse("inventory:ingredient_create"), {
            "name": "Rice", "unit_of_measure": "kg",
            "minimum_stock": "0", "average_unit_cost": "0",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ingredient.objects.filter(name="Rice").count(), 2)

    def test_cashier_cannot_create_ingredient(self):
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_create"), {
            "name": "Rice", "unit_of_measure": "kg",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ingredient.objects.count(), 0)

    def test_tenant_isolation_on_edit(self):
        other_ing = make_ingredient(self.other.pk, name="Other Rice")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("inventory:ingredient_edit", args=[other_ing.pk]))
        self.assertEqual(resp.status_code, 404)


class IngredientEditDeleteTests(InventoryTestBase):
    def test_owner_can_edit(self):
        ing = make_ingredient(self.restaurant.pk, minimum_stock=5)
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_edit", args=[ing.pk]), {
            "name": "Jasmine Rice",
            "unit_of_measure": "kg",
            "minimum_stock": "20",
            "average_unit_cost": "60",
        })
        self.assertEqual(resp.status_code, 302)
        ing.refresh_from_db()
        self.assertEqual(ing.name, "Jasmine Rice")
        self.assertEqual(ing.minimum_stock, Decimal("20"))

    def test_soft_delete_hides_from_list(self):
        ing = make_ingredient(self.restaurant.pk)
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_delete", args=[ing.pk]))
        self.assertEqual(resp.status_code, 302)
        ing.refresh_from_db()
        self.assertTrue(ing.is_deleted)
        resp = self.client.get(reverse("inventory:ingredient_list"))
        self.assertNotContains(resp, "<td>Rice</td>")

    def test_cashier_cannot_delete(self):
        ing = make_ingredient(self.restaurant.pk)
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:ingredient_delete", args=[ing.pk]))
        self.assertEqual(resp.status_code, 302)
        ing.refresh_from_db()
        self.assertFalse(ing.is_deleted)


# ── Transactions (FR-042, FR-043, FR-044, FR-047) ────────────────────


class TransactionModelTests(InventoryTestBase):
    def setUp(self):
        super().setUp()
        self.ing = make_ingredient(self.restaurant.pk, unit_of_measure="kg")

    def test_purchase_raises_stock_and_records_balance(self):
        txn = record(self.ing, InventoryTransaction.Type.PURCHASE, 10, unit_cost=Decimal("50"))
        self.assertEqual(txn.resulting_balance, Decimal("10"))
        self.assertEqual(txn.quantity, Decimal("10"))
        self.assertEqual(self.ing.current_stock, Decimal("10"))

    def test_consumption_decreases_stock(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 4)
        self.assertEqual(self.ing.current_stock, Decimal("6"))

    def test_spoilage_and_return_decrease_stock(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.SPOILAGE, 1)
        record(self.ing, InventoryTransaction.Type.RETURN, 2)
        self.assertEqual(self.ing.current_stock, Decimal("7"))

    def test_adjustment_in_and_out(self):
        record(self.ing, InventoryTransaction.Type.ADJUSTMENT, 5)
        record(self.ing, InventoryTransaction.Type.ADJUSTMENT, -2)
        self.assertEqual(self.ing.current_stock, Decimal("3"))

    def test_outgoing_sign_is_normalized(self):
        # Spoilages entered with a positive quantity are stored as negative.
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        txn = record(self.ing, InventoryTransaction.Type.SPOILAGE, 2)
        self.assertEqual(txn.quantity, Decimal("-2"))
        self.assertEqual(self.ing.current_stock, Decimal("8"))

    def test_negative_stock_rejected_with_descriptive_error(self):
        """FR-044: reject with ingredient name and shortfall."""
        record(self.ing, InventoryTransaction.Type.PURCHASE, 3)
        with self.assertRaises(ValidationError) as ctx:
            record(self.ing, InventoryTransaction.Type.CONSUMPTION, 5)
        msg = str(ctx.exception)
        self.assertIn("Rice", msg)
        self.assertIn("-2", msg)

    def test_transaction_records_reference_and_user(self):
        txn = record(
            self.ing, InventoryTransaction.Type.PURCHASE, 10,
            reference="PO-001", user=self.owner,
        )
        self.assertEqual(txn.reference, "PO-001")
        self.assertEqual(txn.user, self.owner)

    def test_transaction_is_immutable(self):
        txn = record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        with self.assertRaises(ValidationError):
            txn.delete()
        self.assertEqual(self.ing.transactions.count(), 1)

    def test_weighted_average_cost(self):
        """FR-047: (50*10 + 60*10)/20 = 55."""
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10, unit_cost=Decimal("50"))
        self.assertEqual(self.ing.average_unit_cost, Decimal("50"))
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10, unit_cost=Decimal("60"))
        self.ing.refresh_from_db()
        self.assertEqual(self.ing.average_unit_cost, Decimal("55"))

    def test_first_purchase_sets_average_cost(self):
        self.ing.average_unit_cost = Decimal("0")
        self.ing.save()
        record(self.ing, InventoryTransaction.Type.PURCHASE, 5, unit_cost=Decimal("80"))
        self.ing.refresh_from_db()
        self.assertEqual(self.ing.average_unit_cost, Decimal("80"))

    def test_non_purchase_does_not_change_average_cost(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10, unit_cost=Decimal("50"))
        record(self.ing, InventoryTransaction.Type.ADJUSTMENT, 5, unit_cost=Decimal("1"))
        self.ing.refresh_from_db()
        self.assertEqual(self.ing.average_unit_cost, Decimal("50"))


class TransactionFormTests(InventoryTestBase):
    def setUp(self):
        super().setUp()
        self.ing = make_ingredient(self.restaurant.pk)

    def test_reason_required_for_adjustment(self):
        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.ADJUSTMENT,
                "quantity": "5",
                "direction": "OUT",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["reason"])

    def test_reason_required_for_spoilage(self):
        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.SPOILAGE,
                "quantity": "1",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["reason"])

    def test_unit_cost_required_for_purchase(self):
        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.PURCHASE,
                "quantity": "10",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors["unit_cost"])

    def test_save_signs_quantity_by_type(self):
        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.PURCHASE,
                "quantity": "10",
                "unit_cost": "50",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertTrue(form.is_valid())
        txn = form.save()
        self.assertEqual(txn.quantity, Decimal("10"))

        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.RETURN,
                "quantity": "2",
                "reason": "Damaged batch",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertTrue(form.is_valid())
        txn = form.save()
        self.assertEqual(txn.quantity, Decimal("-2"))

    def test_adjustment_direction(self):
        form = IngredientTransactionForm(
            data={
                "ingredient": self.ing.pk,
                "transaction_type": InventoryTransaction.Type.ADJUSTMENT,
                "quantity": "3",
                "direction": "IN",
                "reason": "Found extra stock",
            },
            restaurant_id=self.restaurant.pk,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save().quantity, Decimal("3"))


class TransactionViewTests(InventoryTestBase):
    def setUp(self):
        super().setUp()
        self.ing = make_ingredient(self.restaurant.pk)

    def test_owner_records_movement(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:transaction_create"), {
            "ingredient": self.ing.pk,
            "transaction_type": InventoryTransaction.Type.PURCHASE,
            "quantity": "10",
            "unit_cost": "50",
            "reference": "PO-001",
        })
        self.assertEqual(resp.status_code, 302)
        txn = self.ing.transactions.get()
        self.assertEqual(txn.resulting_balance, Decimal("10"))
        self.assertEqual(txn.user, self.owner)

    def test_insufficient_stock_shows_error_not_crash(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 2)
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:transaction_create"), {
            "ingredient": self.ing.pk,
            "transaction_type": InventoryTransaction.Type.CONSUMPTION,
            "quantity": "5",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Insufficient stock")
        self.assertEqual(self.ing.transactions.count(), 1)

    def test_cashier_cannot_record_movement(self):
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.post(reverse("inventory:transaction_create"), {
            "ingredient": self.ing.pk,
            "transaction_type": InventoryTransaction.Type.PURCHASE,
            "quantity": "10",
            "unit_cost": "50",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.ing.transactions.count(), 0)

    def test_cashier_can_view_ingredients_and_stock_card(self):
        """SRS role matrix: Cashier/Kitchen have read access to inventory."""
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.get(reverse("inventory:ingredient_list"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("inventory:stock_card", args=[self.ing.pk]))
        self.assertEqual(resp.status_code, 200)


# ── Low Stock Alerts (FR-045) ────────────────────────────────────────


class LowStockAlertTests(InventoryTestBase):
    def setUp(self):
        super().setUp()
        self.ing = make_ingredient(self.restaurant.pk, minimum_stock=5)

    def test_alert_created_at_or_below_minimum(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        self.assertEqual(LowStockAlert.objects.count(), 0)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 5)
        self.assertEqual(LowStockAlert.objects.count(), 1)

    def test_only_one_open_alert_until_replenished(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 6)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 1)
        open_alerts = LowStockAlert.objects.filter(resolved_at__isnull=True)
        self.assertEqual(open_alerts.count(), 1)

    def test_alert_resolved_when_restocked_above_threshold(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 6)
        self.assertEqual(LowStockAlert.objects.filter(resolved_at__isnull=True).count(), 1)
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        self.assertEqual(LowStockAlert.objects.filter(resolved_at__isnull=True).count(), 0)

    def test_alert_reopens_after_second_drop(self):
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 6)
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10)
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 11)
        open_alerts = LowStockAlert.objects.filter(resolved_at__isnull=True)
        self.assertEqual(open_alerts.count(), 1)

    def test_alerts_are_tenant_scoped(self):
        other_ing = make_ingredient(self.other.pk, name="Other", minimum_stock=5)
        record(other_ing, InventoryTransaction.Type.PURCHASE, 1)
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("inventory:ingredient_list"))
        self.assertNotContains(resp, "Other")


# ── Stock Card (FR-046) ──────────────────────────────────────────────


class StockCardTests(InventoryTestBase):
    def setUp(self):
        super().setUp()
        self.ing = make_ingredient(self.restaurant.pk)
        record(self.ing, InventoryTransaction.Type.PURCHASE, 10, reference="PO-1")
        record(self.ing, InventoryTransaction.Type.CONSUMPTION, 3, reference="ORDER-7")
        record(self.ing, InventoryTransaction.Type.SPOILAGE, 1, reason="Leak")

    def test_stock_card_shows_ledger(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("inventory:stock_card", args=[self.ing.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "PO-1")
        self.assertContains(resp, "ORDER-7")
        self.assertContains(resp, "Leak")

    def test_stock_card_filters_by_type(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(
            reverse("inventory:stock_card", args=[self.ing.pk]),
            {"type": InventoryTransaction.Type.PURCHASE},
        )
        self.assertContains(resp, "PO-1")
        self.assertNotContains(resp, "ORDER-7")

    def test_stock_card_tenant_isolation(self):
        other_ing = make_ingredient(self.other.pk, name="Other")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("inventory:stock_card", args=[other_ing.pk]))
        self.assertEqual(resp.status_code, 404)
