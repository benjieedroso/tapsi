from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from menu.models import Category, MenuItem, MenuItemPriceHistory
from menu.tests.base import MenuAPITestBase


# ── CREATE ────────────────────────────────────────────────────────────

class MenuItemCreateAPITests(MenuAPITestBase):

    def setUp(self):
        super().setUp()
        self.cat = self.make_category(name="Silog")

    def test_owner_can_create_menu_item(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog",
            "description": "Beef tapa with rice and egg",
            "category": self.cat.pk,
            "price": "75.00",
            "prep_minutes": 10,
            "is_available": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        item = MenuItem.objects.get(pk=resp.data["id"])
        self.assertEqual(item.name, "Tapsilog")
        self.assertEqual(item.price, Decimal("75.00"))
        self.assertEqual(item.restaurant_id, self.restaurant.pk)

    def test_name_required(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "", "price": "75.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_name_min_2_chars(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "T", "price": "75.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_name_trims_whitespace(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "  Tapsilog  ", "price": "75.00", "prep_minutes": 10,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        item = MenuItem.objects.get(pk=resp.data["id"])
        self.assertEqual(item.name, "Tapsilog")

    def test_price_required(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {"name": "Tapsilog"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.data)

    def test_price_cannot_be_negative(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "-10.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.data)

    def test_price_zero_allowed(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "0.00", "prep_minutes": 10,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_prep_minutes_min_1(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "75.00", "prep_minutes": 0,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("prep_minutes", resp.data)

    def test_cannot_attach_category_from_other_restaurant(self):
        other_cat = self.make_category(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "75.00", "category": other_cat.pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", resp.data)

    def test_response_shape(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "75.00", "prep_minutes": 10,
        })
        for key in ["id", "name", "price", "prep_minutes",
                    "is_available", "is_deleted", "restaurant_id"]:
            self.assertIn(key, resp.data)


# ── LIST ──────────────────────────────────────────────────────────────

class MenuItemListAPITests(MenuAPITestBase):

    def test_list_only_own_restaurant_items(self):
        self.make_menu_item(name="Mine")
        self.make_menu_item(name="Theirs", restaurant=self.other_restaurant)

        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:menuitem-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        results = resp.data["results"] if "results" in resp.data else resp.data
        names = [i["name"] for i in results]
        self.assertIn("Mine", names)
        self.assertNotIn("Theirs", names)

    def test_soft_deleted_items_hidden(self):
        visible = self.make_menu_item(name="Visible")
        hidden = self.make_menu_item(name="Hidden")
        hidden.soft_delete()

        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:menuitem-list"))
        results = resp.data["results"] if "results" in resp.data else resp.data
        names = [i["name"] for i in results]
        self.assertIn("Visible", names)
        self.assertNotIn("Hidden", names)


# ── RETRIEVE ──────────────────────────────────────────────────────────

class MenuItemRetrieveAPITests(MenuAPITestBase):

    def test_owner_can_retrieve_own_item(self):
        item = self.make_menu_item(name="Tapsilog")
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:menuitem-detail", args=[item.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Tapsilog")

    def test_cannot_retrieve_other_restaurants_item(self):
        other_item = self.make_menu_item(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:menuitem-detail", args=[other_item.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── UPDATE ────────────────────────────────────────────────────────────

class MenuItemUpdateAPITests(MenuAPITestBase):

    def test_owner_can_update_menu_item(self):
        item = self.make_menu_item(name="Tapsilog")
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:menuitem-detail", args=[item.pk]),
            {"name": "Tapsilog Deluxe"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.name, "Tapsilog Deluxe")

    def test_price_change_creates_history_entry(self):
        item = self.make_menu_item(name="Tapsilog", price="75.00")
        self.authenticate(self.owner)
        self.client.patch(
            reverse("menu:menuitem-detail", args=[item.pk]),
            {"price": "85.00"},
        )
        item.refresh_from_db()
        self.assertEqual(item.price, Decimal("85.00"))
        history = MenuItemPriceHistory.objects.filter(menu_item=item)
        self.assertEqual(history.count(), 1)
        entry = history.first()
        self.assertEqual(entry.old_price, Decimal("75.00"))
        self.assertEqual(entry.new_price, Decimal("85.00"))

    def test_same_price_no_history(self):
        item = self.make_menu_item(name="Tapsilog", price="75.00")
        self.authenticate(self.owner)
        self.client.patch(
            reverse("menu:menuitem-detail", args=[item.pk]),
            {"price": "75.00"},
        )
        self.assertEqual(MenuItemPriceHistory.objects.filter(menu_item=item).count(), 0)

    def test_cannot_update_other_restaurants_item(self):
        other_item = self.make_menu_item(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:menuitem-detail", args=[other_item.pk]),
            {"name": "Hijack"},
        )
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── DELETE (SOFT) ─────────────────────────────────────────────────────

class MenuItemDeleteAPITests(MenuAPITestBase):

    def test_delete_soft_deletes(self):
        item = self.make_menu_item(name="Tapsilog")
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:menuitem-detail", args=[item.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        item.refresh_from_db()
        self.assertTrue(item.is_deleted)
        self.assertIsNotNone(item.deleted_at)

    def test_cannot_delete_other_restaurants_item(self):
        other_item = self.make_menu_item(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:menuitem-detail", args=[other_item.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        other_item.refresh_from_db()
        self.assertFalse(other_item.is_deleted)


# ── ACCESS ────────────────────────────────────────────────────────────

class MenuItemAccessAPITests(MenuAPITestBase):

    def test_cashier_cannot_create_menu_item(self):
        self.authenticate(self.cashier)
        resp = self.client.post(reverse("menu:menuitem-list"), {
            "name": "Tapsilog", "price": "75.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_update_menu_item(self):
        item = self.make_menu_item(name="Tapsilog")
        self.authenticate(self.cashier)
        resp = self.client.patch(
            reverse("menu:menuitem-detail", args=[item.pk]),
            {"name": "Hijack"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_delete_menu_item(self):
        item = self.make_menu_item(name="Tapsilog")
        self.authenticate(self.cashier)
        resp = self.client.delete(reverse("menu:menuitem-detail", args=[item.pk]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_blocked(self):
        resp = self.client.get(reverse("menu:menuitem-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)