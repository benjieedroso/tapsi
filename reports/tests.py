from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User
from expenses.models import Expense
from inventory.models import Ingredient, InventoryTransaction
from menu.models import AddOn, Category, MenuItem
from orders.models import Order, OrderItem, OrderItemAddon, Payment
from orders.services import record_payment, settle_order
from recipes.models import Recipe, RecipeIngredient

from .views import _daily_sales_data, _monthly_data, _pandl_data, _tax_data


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class ReportsBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.today = timezone.localdate()
        self.category = Category.objects.create(restaurant_id=self.rid, name="Rice Meals")
        self.menu_item = MenuItem.objects.create(
            restaurant_id=self.rid, category=self.category,
            name="Chicken Adobo", price=Decimal("100"),
        )
        self.rice = Ingredient.objects.create(
            restaurant_id=self.rid, name="Rice", unit_of_measure="kg",
            average_unit_cost=Decimal("50"),
        )
        self.chicken = Ingredient.objects.create(
            restaurant_id=self.rid, name="Chicken", unit_of_measure="kg",
            average_unit_cost=Decimal("180"),
        )
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Adobo Recipe",
        )
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.rice, quantity=Decimal("0.2"))
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.chicken, quantity=Decimal("0.3"))

    def _stock(self, ingredient, qty):
        InventoryTransaction.objects.create(
            ingredient=ingredient,
            transaction_type=InventoryTransaction.Type.PURCHASE,
            quantity=qty, unit_cost=ingredient.average_unit_cost,
        )

    def _completed_order(self, qty=1):
        self._stock(self.rice, 5)
        self._stock(self.chicken, 5)
        order = Order.objects.create(
            restaurant_id=self.rid, order_type=Order.Type.TAKE_OUT,
            created_by=self.owner,
        )
        order.order_number = f"#{Order.objects.filter(restaurant_id=self.rid).count():04d}"
        order.save(update_fields=["order_number"])
        item = OrderItem.objects.create(
            order=order, menu_item=self.menu_item,
            item_name=self.menu_item.name, unit_price=self.menu_item.price, quantity=qty,
        )
        order.recompute_totals()
        record_payment(order, Payment.Method.CASH, order.total, self.owner)
        settle_order(order, self.owner)
        order.refresh_from_db()
        return order


class ReportDataTests(ReportsBase):
    def test_daily_sales_totals(self):
        """FR-130: gross, discounts, net, VAT, orders, AOV."""
        self._completed_order(qty=1)
        data = _daily_sales_data(self.rid, self.today)
        self.assertEqual(data["gross"], Decimal("100.00"))
        self.assertEqual(data["net"], Decimal("100.00"))
        self.assertEqual(data["vat"], Decimal("12.00"))  # 12% of VATable 100
        self.assertEqual(data["order_count"], 1)
        self.assertEqual(data["aov"], Decimal("100.00"))
        self.assertEqual(data["method_breakdown"]["Cash"], Decimal("100.00"))

    def test_daily_sales_excludes_open_orders(self):
        """FR-139: only immutable COMPLETED records count."""
        self._completed_order()
        order = Order.objects.create(
            restaurant_id=self.rid, order_type=Order.Type.TAKE_OUT, created_by=self.owner,
        )
        order.order_number = "#0099"
        order.save(update_fields=["order_number"])
        OrderItem.objects.create(
            order=order, menu_item=self.menu_item,
            item_name="Chicken Adobo", unit_price=Decimal("100"), quantity=1,
        )
        order.recompute_totals()
        data = _daily_sales_data(self.rid, self.today)
        self.assertEqual(data["order_count"], 1)
        self.assertEqual(data["net"], Decimal("100.00"))

    def test_pandl_includes_cogs_and_expenses(self):
        """FR-133: net sales − COGS − expenses = profit."""
        self._completed_order()
        Expense.objects.create(
            restaurant_id=self.rid, category=Expense.Category.WATER,
            amount=Decimal("30"), expense_date=self.today,
            status=Expense.Status.APPROVED, payment_method="CASH", created_by=self.owner,
        )
        data = _pandl_data(self.rid, self.today, self.today)
        self.assertEqual(data["net_sales"], Decimal("100.00"))
        self.assertEqual(data["cogs"], Decimal("64.00"))  # 0.2×50 + 0.3×180
        self.assertEqual(data["expenses"], Decimal("30.00"))
        self.assertEqual(data["profit"], Decimal("6.00"))

    def test_tax_summary(self):
        self._completed_order()
        data = _tax_data(self.rid, self.today, self.today)
        self.assertEqual(data["vatable"], Decimal("100.00"))
        self.assertEqual(data["output_vat"], Decimal("12.00"))

    def test_monthly_totals(self):
        self._completed_order()
        data = _monthly_data(self.rid, self.today.replace(day=1))
        self.assertEqual(data["month_total"], Decimal("100.00"))
        self.assertEqual(data["days"][0]["total"], Decimal("100.00"))


class ReportViewTests(ReportsBase):
    def test_views_require_manager_role(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)
        for name in ("daily_sales", "profit_loss", "tax_summary"):
            response = self.client.get(reverse(f"reports:{name}"))
            self.assertEqual(response.status_code, 302)

    def test_daily_sales_csv_export(self):
        self._completed_order()
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("reports:daily_sales"),
            {"date": self.today.isoformat(), "export": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(b"Gross sales", response.content)
        self.assertIn(b"100.00", response.content)

    def test_product_mix_ranking(self):
        self._completed_order(qty=3)
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("reports:product_mix"),
            {"start": self.today.isoformat(), "end": self.today.isoformat()},
        )
        self.assertContains(response, "Chicken Adobo")
        self.assertContains(response, "3")
