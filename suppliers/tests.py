from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Restaurant, User
from inventory.models import Ingredient, InventoryTransaction

from .forms import PurchaseOrderForm, SupplierForm, SupplierPaymentForm
from .models import PurchaseOrder, PurchaseOrderItem, Supplier, SupplierPayment


def _make_owner():
    """Owner user bound to a real restaurant (restaurant_id is the tenant key)."""
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class SupplierModelTests(TestCase):
    def setUp(self):
        self.restaurant, self.user = _make_owner()
        self.rid = self.user.restaurant_id

    def test_outstanding_balance_is_received_minus_paid(self):
        supplier = Supplier.objects.create(restaurant_id=self.rid, name="Rice Depot")
        ingredient = Ingredient.objects.create(restaurant_id=self.rid, name="Rice", unit_of_measure="kg")
        po = PurchaseOrder.objects.create(restaurant_id=self.rid, supplier=supplier, placed_by=self.user)
        PurchaseOrderItem.objects.create(
            purchase_order=po, ingredient=ingredient, qty_ordered=10, unit_cost=Decimal("50"),
        )
        self.assertEqual(supplier.outstanding_balance, Decimal("0"))
        # Receive 10 units → PURCHASE transaction updates stock.
        txn = InventoryTransaction(
            ingredient=ingredient,
            transaction_type=InventoryTransaction.Type.PURCHASE,
            quantity=10, unit_cost=Decimal("50"),
            reference=po.po_number, user=self.user,
        )
        txn.save()
        po.items.update(qty_received=10)
        po.status = PurchaseOrder.Status.RECEIVED
        po.save(update_fields=["status"])
        self.assertEqual(supplier.outstanding_balance, Decimal("500"))
        SupplierPayment.objects.create(
            restaurant_id=self.rid, supplier=supplier, amount=Decimal("200"),
            payment_date="2026-08-04", recorded_by=self.user,
        )
        self.assertEqual(supplier.outstanding_balance, Decimal("300"))


class SupplierFormTests(TestCase):
    def setUp(self):
        self.restaurant, self.user = _make_owner()
        self.rid = self.user.restaurant_id

    def test_name_required_and_min_length(self):
        form = SupplierForm(data={"name": "  "}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

        form = SupplierForm(data={"name": "X"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_name_unique_per_restaurant(self):
        Supplier.objects.create(restaurant_id=self.rid, name="Rice Depot")
        form = SupplierForm(data={"name": "  rice depot  "}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class SupplierViewTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.client.force_login(self.owner)

    def test_cashier_cannot_access_suppliers(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant_id=self.rid, role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse("suppliers:supplier_list"))
        self.assertEqual(response.status_code, 302)

    def test_delete_without_pos_hard_deletes(self):
        supplier = Supplier.objects.create(restaurant_id=self.rid, name="Depot")
        self.client.post(reverse("suppliers:supplier_delete", args=[supplier.pk]))
        self.assertFalse(Supplier.objects.filter(pk=supplier.pk).exists())

    def test_delete_with_pos_soft_deletes(self):
        """FR-053: supplier with purchase history is deactivated, not deleted."""
        supplier = Supplier.objects.create(restaurant_id=self.rid, name="Depot")
        PurchaseOrder.objects.create(restaurant_id=self.rid, supplier=supplier, placed_by=self.owner)
        self.client.post(reverse("suppliers:supplier_delete", args=[supplier.pk]))
        supplier.refresh_from_db()
        self.assertTrue(supplier.is_deleted)


class PurchaseOrderTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.supplier = Supplier.objects.create(restaurant_id=self.rid, name="Rice Depot")
        self.ingredient = Ingredient.objects.create(restaurant_id=self.rid, name="Rice", unit_of_measure="kg")

    def _make_po(self, with_item=True):
        po = PurchaseOrder.objects.create(restaurant_id=self.rid, supplier=self.supplier, placed_by=self.owner)
        if with_item:
            PurchaseOrderItem.objects.create(
                purchase_order=po, ingredient=self.ingredient,
                qty_ordered=10, unit_cost=Decimal("50"),
            )
        return po

    def test_po_number_sequential_per_restaurant(self):
        po1 = self._make_po()
        self.assertRegex(po1.po_number, r"^PO-2026-00001$")
        po2 = self._make_po()
        self.assertRegex(po2.po_number, r"^PO-2026-00002$")

    def test_receive_creates_purchase_transactions_and_stock(self):
        """FR-062: receiving writes PURCHASE ledger entries (weighted avg cost)."""
        po = self._make_po()
        po.status = PurchaseOrder.Status.ORDERED
        po.save(update_fields=["status"])
        item = po.items.first()
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("suppliers:po_receive", args=[po.pk]),
            {f"received_{item.pk}": "10"},
        )
        self.assertRedirects(response, reverse("suppliers:po_detail", args=[po.pk]))
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrder.Status.RECEIVED)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 10)
        self.assertEqual(self.ingredient.average_unit_cost, Decimal("50"))
        txn = InventoryTransaction.objects.get(reference=po.po_number)
        self.assertEqual(txn.transaction_type, InventoryTransaction.Type.PURCHASE)
        self.assertEqual(txn.quantity, 10)

    def test_receive_rejects_over_receiving(self):
        po = self._make_po()
        po.status = PurchaseOrder.Status.ORDERED
        po.save(update_fields=["status"])
        item = po.items.first()
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("suppliers:po_receive", args=[po.pk]),
            {f"received_{item.pk}": "15"},
        )
        self.assertRedirects(response, reverse("suppliers:po_detail", args=[po.pk]))
        item.refresh_from_db()
        self.assertEqual(item.qty_received, 0)
        self.assertEqual(InventoryTransaction.objects.filter(reference=po.po_number).count(), 0)

    def test_receive_only_from_ordered(self):
        po = self._make_po()
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("suppliers:po_receive", args=[po.pk]),
            {f"received_{po.items.first().pk}": "10"},
        )
        self.assertRedirects(response, reverse("suppliers:po_detail", args=[po.pk]))
        self.assertEqual(po.items.first().qty_received, 0)

    def test_place_requires_items(self):
        po = self._make_po(with_item=False)
        self.client.force_login(self.owner)
        self.client.post(reverse("suppliers:po_place", args=[po.pk]))
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrder.Status.DRAFT)
        po2 = self._make_po()
        self.client.post(reverse("suppliers:po_place", args=[po2.pk]))
        po2.refresh_from_db()
        self.assertEqual(po2.status, PurchaseOrder.Status.ORDERED)

    def test_cancel_allowed_from_draft_and_ordered_only(self):
        po = self._make_po()
        self.client.force_login(self.owner)
        self.client.post(reverse("suppliers:po_cancel", args=[po.pk]))
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrder.Status.CANCELLED)

    def test_edit_blocked_outside_draft(self):
        po = self._make_po()
        po.status = PurchaseOrder.Status.ORDERED
        po.save(update_fields=["status"])
        self.client.force_login(self.owner)
        response = self.client.get(reverse("suppliers:po_edit", args=[po.pk]))
        self.assertRedirects(response, reverse("suppliers:po_detail", args=[po.pk]))

    def test_item_received_cannot_exceed_ordered(self):
        po = self._make_po()
        item = po.items.first()
        item.qty_received = 10
        item.save()
        item.qty_received = 11
        with self.assertRaises(Exception):
            item.save()


class PurchaseOrderFormTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.supplier = Supplier.objects.create(restaurant_id=self.rid, name="Depot")
        self.ingredient = Ingredient.objects.create(restaurant_id=self.rid, name="Rice", unit_of_measure="kg")

    def test_line_quantity_required_with_ingredient(self):
        form = PurchaseOrderForm(
            data={"supplier": self.supplier.pk, "line_ingredient": self.ingredient.pk,
                  "line_unit_cost": "50"},
            restaurant_id=self.rid,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("line_quantity", form.errors)
