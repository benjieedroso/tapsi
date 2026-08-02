from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Restaurant, User

from .models import AddOn, Category, MenuItem, MenuItemAddOn, MenuItemPriceHistory
from .forms import CategoryForm, MenuItemForm, AddOnForm


class MenuTestBase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Testaurant")
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass1234",
            first_name="Own", last_name="Er",
            restaurant=self.restaurant, role=User.Role.OWNER,
        )
        self.cashier = User.objects.create_user(
            email="cashier@test.com", password="testpass1234",
            first_name="Ca", last_name="Shier",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client = Client()


# ── Category Tests (FR-030) ──────────────────────────────────────────


class CategoryCreateTests(MenuTestBase):
    def test_owner_can_create_category(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {
            "name": "Silog Meals",
            "display_order": "1",
            "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Category.objects.count(), 1)
        cat = Category.objects.first()
        self.assertEqual(cat.name, "Silog Meals")
        self.assertEqual(cat.restaurant_id, self.restaurant.pk)

    def test_category_name_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": ""})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_category_name_min_2_chars(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": "A"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_category_name_unique_per_restaurant(self):
        Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": "Silog"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_category_name_case_insensitive_unique(self):
        Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": "silog"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_category_name_trims_whitespace(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        self.client.post(reverse("menu:category_create"), {"name": "  Silog  ", "display_order": "0"})
        cat = Category.objects.first()
        self.assertEqual(cat.name, "Silog")

    def test_category_display_order_cannot_be_negative(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {
            "name": "Silog",
            "display_order": "-1",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["display_order"])

    def test_same_category_name_allowed_in_different_restaurant(self):
        r2 = Restaurant.objects.create(name="Other")
        Category.objects.create(restaurant_id=r2.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": "Silog", "display_order": "0"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Category.objects.filter(restaurant_id=self.restaurant.pk).count(), 1)


class CategoryEditTests(MenuTestBase):
    def test_owner_can_edit_category(self):
        cat = Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_edit", args=[cat.pk]), {
            "name": "Breakfast",
            "display_order": "0",
            "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "Breakfast")

    def test_cannot_edit_other_restaurants_category(self):
        r2 = Restaurant.objects.create(name="Other")
        cat2 = Category.objects.create(restaurant_id=r2.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_edit", args=[cat2.pk]), {"name": "Hijack"})
        self.assertEqual(resp.status_code, 404)


class CategoryDeleteTests(MenuTestBase):
    def test_owner_can_delete_category(self):
        cat = Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_delete", args=[cat.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_delete_category_unassigns_items(self):
        cat = Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        item = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, category=cat,
            name="Tapsilog", price=Decimal("75.00"),
        )
        self.client.login(email="owner@test.com", password="testpass1234")
        self.client.post(reverse("menu:category_delete", args=[cat.pk]))
        item.refresh_from_db()
        self.assertIsNone(item.category)


class CategoryAccessTests(MenuTestBase):
    def test_cashier_cannot_create_category(self):
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.get(reverse("menu:category_create"))
        self.assertEqual(resp.status_code, 302)

    def test_manager_can_create_category(self):
        manager = User.objects.create_user(
            email="manager@test.com", password="testpass1234",
            first_name="Man", last_name="Ager",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        self.client.login(email="manager@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:category_create"), {"name": "Silog", "display_order": "0"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Category.objects.count(), 1)


# ── Menu Item Tests (FR-031, FR-034, FR-035) ─────────────────────────


class MenuItemCreateTests(MenuTestBase):
    def setUp(self):
        super().setUp()
        self.cat = Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")

    def test_owner_can_create_menu_item(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
            "description": "Beef tapa with rice and egg",
            "category": str(self.cat.pk),
            "price": "75.00",
            "prep_minutes": "10",
            "is_available": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MenuItem.objects.count(), 1)
        item = MenuItem.objects.first()
        self.assertEqual(item.name, "Tapsilog")
        self.assertEqual(item.price, Decimal("75.00"))

    def test_menu_item_name_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "",
            "price": "75.00",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_menu_item_name_min_2_chars(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "T",
            "price": "75.00",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_menu_item_price_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["price"])

    def test_menu_item_price_cannot_be_negative(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
            "price": "-10.00",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["price"])

    def test_menu_item_price_zero_allowed(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
            "price": "0.00",
            "prep_minutes": "10",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MenuItem.objects.first().price, Decimal("0.00"))

    def test_menu_item_prep_minutes_min_1(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
            "price": "75.00",
            "prep_minutes": "0",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["prep_minutes"])

    def test_menu_item_name_trims_whitespace(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        self.client.post(reverse("menu:menu_create"), {
            "name": "  Tapsilog  ",
            "price": "75.00",
            "prep_minutes": "10",
        })
        item = MenuItem.objects.first()
        self.assertEqual(item.name, "Tapsilog")

    def test_menu_item_description_max_length(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_create"), {
            "name": "Tapsilog",
            "price": "75.00",
            "description": "x" * 1001,
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["description"])


class MenuItemToggleAvailabilityTests(MenuTestBase):
    def setUp(self):
        super().setUp()
        self.item = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"), is_available=True,
        )

    def test_toggle_availability_hides_item(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_toggle", args=[self.item.pk]),
                                HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_available"])

    def test_toggle_availability_shows_item(self):
        self.item.is_available = False
        self.item.save()
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_toggle", args=[self.item.pk]),
                                HTTP_ACCEPT="application/json")
        data = resp.json()
        self.assertTrue(data["is_available"])


class MenuItemSoftDeleteTests(MenuTestBase):
    def setUp(self):
        super().setUp()
        self.item = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"),
        )

    def test_soft_delete_sets_fields(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_delete", args=[self.item.pk]))
        self.assertEqual(resp.status_code, 302)
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_deleted)
        self.assertIsNotNone(self.item.deleted_at)

    def test_soft_deleted_item_hidden_from_list(self):
        self.item.soft_delete()
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("menu:menu_list"))
        items = resp.context["items"]
        self.assertNotIn(self.item, items)


class MenuItemPriceHistoryTests(MenuTestBase):
    def setUp(self):
        super().setUp()
        self.item = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"),
        )

    def test_price_change_creates_history(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        self.client.post(reverse("menu:menu_edit", args=[self.item.pk]), {
            "name": "Tapsilog",
            "price": "85.00",
            "prep_minutes": "10",
            "is_available": "on",
        })
        self.item.refresh_from_db()
        self.assertEqual(self.item.price, Decimal("85.00"))
        history = MenuItemPriceHistory.objects.filter(menu_item=self.item)
        self.assertEqual(history.count(), 1)
        entry = history.first()
        self.assertEqual(entry.old_price, Decimal("75.00"))
        self.assertEqual(entry.new_price, Decimal("85.00"))

    def test_same_price_no_history(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        self.client.post(reverse("menu:menu_edit", args=[self.item.pk]), {
            "name": "Tapsilog",
            "price": "75.00",
            "prep_minutes": "10",
            "is_available": "on",
        })
        self.assertEqual(MenuItemPriceHistory.objects.filter(menu_item=self.item).count(), 0)


class MenuItemAccessTests(MenuTestBase):
    def test_cashier_cannot_create_menu_item(self):
        self.client.login(email="cashier@test.com", password="testpass1234")
        resp = self.client.get(reverse("menu:menu_create"))
        self.assertEqual(resp.status_code, 302)

    def test_cannot_edit_other_restaurants_item(self):
        r2 = Restaurant.objects.create(name="Other")
        item2 = MenuItem.objects.create(
            restaurant_id=r2.pk, name="Other Item",
            price=Decimal("50.00"),
        )
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:menu_edit", args=[item2.pk]), {
            "name": "Hijack", "price": "10.00", "prep_minutes": "5",
        })
        self.assertEqual(resp.status_code, 404)

    def test_menu_search_by_name(self):
        MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"),
        )
        MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Longsilog",
            price=Decimal("80.00"),
        )
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("menu:menu_list") + "?q=tap")
        items = resp.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().name, "Tapsilog")

    def test_menu_filter_by_category(self):
        cat = Category.objects.create(restaurant_id=self.restaurant.pk, name="Silog")
        item1 = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"), category=cat,
        )
        item2 = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Rice",
            price=Decimal("15.00"),
        )
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.get(reverse("menu:menu_list") + f"?category={cat.pk}")
        items = resp.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first(), item1)


# ── Add-On Tests (FR-033) ────────────────────────────────────────────


class AddOnCreateTests(MenuTestBase):
    def test_owner_can_create_addon(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:addon_create"), {
            "name": "Extra Rice",
            "price": "15.00",
            "is_available": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(AddOn.objects.count(), 1)
        addon = AddOn.objects.first()
        self.assertEqual(addon.name, "Extra Rice")
        self.assertEqual(addon.restaurant_id, self.restaurant.pk)

    def test_addon_name_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:addon_create"), {"name": ""})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_addon_name_min_2_chars(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:addon_create"), {"name": "E"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["name"])

    def test_addon_price_required(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:addon_create"), {"name": "Extra Rice"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["price"])

    def test_addon_price_cannot_be_negative(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(reverse("menu:addon_create"), {
            "name": "Extra Rice",
            "price": "-5.00",
        })
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.errors["price"])


class AddOnToggleTests(MenuTestBase):
    def setUp(self):
        super().setUp()
        self.item = MenuItem.objects.create(
            restaurant_id=self.restaurant.pk, name="Tapsilog",
            price=Decimal("75.00"),
        )
        self.addon = AddOn.objects.create(
            restaurant_id=self.restaurant.pk, name="Extra Rice",
            price=Decimal("15.00"),
        )

    def test_toggle_addon_on(self):
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(
            reverse("menu:menu_toggle_addon", args=[self.item.pk, self.addon.pk]),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["attached"])
        self.assertTrue(MenuItemAddOn.objects.filter(menu_item=self.item, addon=self.addon).exists())

    def test_toggle_addon_off(self):
        MenuItemAddOn.objects.create(menu_item=self.item, addon=self.addon)
        self.client.login(email="owner@test.com", password="testpass1234")
        resp = self.client.post(
            reverse("menu:menu_toggle_addon", args=[self.item.pk, self.addon.pk]),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["attached"])
        self.assertFalse(MenuItemAddOn.objects.filter(menu_item=self.item, addon=self.addon).exists())


# ── Form Validation Unit Tests ────────────────────────────────────────


class CategoryFormTests(TestCase):
    def setUp(self):
        self.rid = 1

    def test_valid_form(self):
        form = CategoryForm(data={"name": "Silog", "display_order": 0, "is_active": True}, restaurant_id=self.rid)
        self.assertTrue(form.is_valid())

    def test_blank_name(self):
        form = CategoryForm(data={"name": ""}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_short_name(self):
        form = CategoryForm(data={"name": "A"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())

    def test_negative_display_order(self):
        form = CategoryForm(data={"name": "Silog", "display_order": -1}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("display_order", form.errors)


class MenuItemFormTests(TestCase):
    def setUp(self):
        self.rid = 1

    def test_valid_form(self):
        form = MenuItemForm(data={
            "name": "Tapsilog", "price": "75.00", "prep_minutes": "10",
        }, restaurant_id=self.rid)
        self.assertTrue(form.is_valid())

    def test_blank_name(self):
        form = MenuItemForm(data={"name": "", "price": "75.00"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_short_name(self):
        form = MenuItemForm(data={"name": "T", "price": "75.00"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())

    def test_negative_price(self):
        form = MenuItemForm(data={"name": "Tapsilog", "price": "-10.00"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_zero_price_valid(self):
        form = MenuItemForm(data={"name": "Tapsilog", "price": "0.00", "prep_minutes": "10"}, restaurant_id=self.rid)
        self.assertTrue(form.is_valid())

    def test_prep_minutes_too_low(self):
        form = MenuItemForm(data={"name": "Tapsilog", "price": "75.00", "prep_minutes": "0"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("prep_minutes", form.errors)


class AddOnFormTests(TestCase):
    def setUp(self):
        self.rid = 1

    def test_valid_form(self):
        form = AddOnForm(data={"name": "Extra Rice", "price": "15.00"}, restaurant_id=self.rid)
        self.assertTrue(form.is_valid())

    def test_blank_name(self):
        form = AddOnForm(data={"name": ""}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())

    def test_short_name(self):
        form = AddOnForm(data={"name": "E"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())

    def test_negative_price(self):
        form = AddOnForm(data={"name": "Extra Rice", "price": "-5.00"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
