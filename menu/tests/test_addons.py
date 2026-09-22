from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from menu.models import AddOn
from menu.tests.base import MenuAPITestBase


# ── CREATE ────────────────────────────────────────────────────────────

class AddOnCreateAPITests(MenuAPITestBase):

    def test_owner_can_create_addon(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "Extra Rice",
            "price": "15.00",
            "is_available": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        addon = AddOn.objects.get(pk=resp.data["id"])
        self.assertEqual(addon.name, "Extra Rice")
        self.assertEqual(addon.price, Decimal("15.00"))
        self.assertEqual(addon.restaurant_id, self.restaurant.pk)

    def test_name_required(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {"name": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_name_min_2_chars(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "E", "price": "15.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_name_trims_whitespace(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "  Extra Rice  ", "price": "15.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        addon = AddOn.objects.get(pk=resp.data["id"])
        self.assertEqual(addon.name, "Extra Rice")

    def test_price_required(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {"name": "Extra Rice"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.data)

    def test_price_cannot_be_negative(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "Extra Rice", "price": "-5.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.data)

    def test_cannot_spoof_restaurant_id(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "Extra Rice", "price": "15.00",
            "restaurant_id": self.other_restaurant.pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        addon = AddOn.objects.get(pk=resp.data["id"])
        self.assertEqual(addon.restaurant_id, self.restaurant.pk)

    def test_response_shape(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "Extra Rice", "price": "15.00",
        })
        for key in ["id", "name", "price", "is_available", "restaurant_id"]:
            self.assertIn(key, resp.data)


# ── LIST ──────────────────────────────────────────────────────────────

class AddOnListAPITests(MenuAPITestBase):

    def test_list_only_own_restaurant_addons(self):
        self.make_addon(name="Mine")
        self.make_addon(name="Theirs", restaurant=self.other_restaurant)

        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:addon-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data["results"] if "results" in resp.data else resp.data
        names = [a["name"] for a in results]
        self.assertIn("Mine", names)
        self.assertNotIn("Theirs", names)


# ── RETRIEVE ──────────────────────────────────────────────────────────

class AddOnRetrieveAPITests(MenuAPITestBase):

    def test_owner_can_retrieve_own_addon(self):
        addon = self.make_addon(name="Extra Rice")
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:addon-detail", args=[addon.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Extra Rice")

    def test_cannot_retrieve_other_restaurants_addon(self):
        other = self.make_addon(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:addon-detail", args=[other.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── UPDATE ────────────────────────────────────────────────────────────

class AddOnUpdateAPITests(MenuAPITestBase):

    def test_owner_can_update_addon(self):
        addon = self.make_addon(name="Extra Rice")
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:addon-detail", args=[addon.pk]),
            {"price": "20.00"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        addon.refresh_from_db()
        self.assertEqual(addon.price, Decimal("20.00"))

    def test_cannot_update_other_restaurants_addon(self):
        other = self.make_addon(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:addon-detail", args=[other.pk]),
            {"name": "Hijack"},
        )
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── DELETE ────────────────────────────────────────────────────────────

class AddOnDeleteAPITests(MenuAPITestBase):

    def test_owner_can_delete_addon(self):
        addon = self.make_addon(name="Extra Rice")
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:addon-detail", args=[addon.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AddOn.objects.filter(pk=addon.pk).exists())

    def test_cannot_delete_other_restaurants_addon(self):
        other = self.make_addon(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:addon-detail", args=[other.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── ACCESS ────────────────────────────────────────────────────────────

class AddOnAccessAPITests(MenuAPITestBase):

    def test_cashier_cannot_create_addon(self):
        self.authenticate(self.cashier)
        resp = self.client.post(reverse("menu:addon-list"), {
            "name": "Extra Rice", "price": "15.00",
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_update_addon(self):
        addon = self.make_addon(name="Extra Rice")
        self.authenticate(self.cashier)
        resp = self.client.patch(
            reverse("menu:addon-detail", args=[addon.pk]),
            {"price": "20.00"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_blocked(self):
        resp = self.client.get(reverse("menu:addon-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)