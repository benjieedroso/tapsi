from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from menu.models import Category, MenuItem
from menu.tests.base import MenuAPITestBase


# ── CREATE ────────────────────────────────────────────────────────────

class CategoryCreateAPITests(MenuAPITestBase):

    def test_owner_can_create_category(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {
            "name": "Silog Meals",
            "display_order": 1,
            "is_active": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(pk=resp.data["id"])
        self.assertEqual(cat.name, "Silog Meals")
        self.assertEqual(cat.restaurant_id, self.restaurant.pk)

    def test_category_name_required(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_category_name_min_2_chars(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": "A"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_category_name_unique_per_restaurant(self):
        self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": "Silog"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_category_name_case_insensitive_unique(self):
        self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": "silog"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_same_category_name_allowed_in_different_restaurant(self):
        self.make_category(name="Silog", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": "Silog"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Category.objects.filter(restaurant_id=self.restaurant.pk).count(), 1
        )

    def test_category_name_trims_whitespace(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {"name": "  Silog  "})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(pk=resp.data["id"])
        self.assertEqual(cat.name, "Silog")

    def test_cannot_spoof_restaurant_id_in_body(self):
        """A malicious client passing restaurant_id must be ignored."""
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {
            "name": "Silog",
            "restaurant_id": self.other_restaurant.pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(pk=resp.data["id"])
        self.assertEqual(cat.restaurant_id, self.restaurant.pk)

    def test_response_contains_expected_fields(self):
        self.authenticate(self.owner)
        resp = self.client.post(reverse("menu:category-list"), {
            "name": "Silog",
            "display_order": 1,
            "is_active": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        for key in ["id", "name", "display_order", "is_active", "restaurant_id"]:
            self.assertIn(key, resp.data)


# ── LIST ──────────────────────────────────────────────────────────────

class CategoryListAPITests(MenuAPITestBase):

    def test_list_returns_only_own_restaurant_categories(self):
        mine = self.make_category(name="Mine")
        theirs = self.make_category(name="Theirs", restaurant=self.other_restaurant)

        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        names = [c["name"] for c in resp.data["results"]] if "results" in resp.data else [c["name"] for c in resp.data]
        self.assertIn("Mine", names)
        self.assertNotIn("Theirs", names)

    def test_list_respects_model_ordering(self):
        self.make_category(name="B", display_order=2)
        self.make_category(name="A", display_order=1)
        self.make_category(name="C", display_order=3)

        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        results = resp.data["results"] if "results" in resp.data else resp.data
        names = [c["name"] for c in results]
        self.assertEqual(names, ["A", "B", "C"])


# ── RETRIEVE ──────────────────────────────────────────────────────────

class CategoryRetrieveAPITests(MenuAPITestBase):

    def test_owner_can_retrieve_own_category(self):
        cat = self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:category-detail", args=[cat.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Silog")

    def test_cannot_retrieve_other_restaurants_category(self):
        other_cat = self.make_category(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.get(reverse("menu:category-detail", args=[other_cat.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── UPDATE ────────────────────────────────────────────────────────────

class CategoryUpdateAPITests(MenuAPITestBase):

    def test_owner_can_update_category(self):
        cat = self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:category-detail", args=[cat.pk]),
            {"name": "Breakfast"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "Breakfast")

    def test_update_still_enforces_uniqueness(self):
        self.make_category(name="Silog")
        cat2 = self.make_category(name="Other")
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:category-detail", args=[cat2.pk]),
            {"name": "Silog"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", resp.data)

    def test_update_keeping_same_name_succeeds(self):
        """Updating a category with its own name must not trip uniqueness."""
        cat = self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:category-detail", args=[cat.pk]),
            {"name": "Silog", "display_order": 5},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cannot_update_other_restaurants_category(self):
        other_cat = self.make_category(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.patch(
            reverse("menu:category-detail", args=[other_cat.pk]),
            {"name": "Hijack"},
        )
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])


# ── DELETE ────────────────────────────────────────────────────────────

class CategoryDeleteAPITests(MenuAPITestBase):

    def test_owner_can_delete_category(self):
        cat = self.make_category(name="Silog")
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:category-detail", args=[cat.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_delete_unassigns_menu_items(self):
        cat = self.make_category(name="Silog")
        item = self.make_menu_item(name="Tapsilog", category=cat)
        self.authenticate(self.owner)
        self.client.delete(reverse("menu:category-detail", args=[cat.pk]))
        item.refresh_from_db()
        self.assertIsNone(item.category)

    def test_cannot_delete_other_restaurants_category(self):
        other_cat = self.make_category(name="Other", restaurant=self.other_restaurant)
        self.authenticate(self.owner)
        resp = self.client.delete(reverse("menu:category-detail", args=[other_cat.pk]))
        self.assertIn(resp.status_code,
                      [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        self.assertTrue(Category.objects.filter(pk=other_cat.pk).exists())


# ── ACCESS / AUTH ─────────────────────────────────────────────────────

class CategoryAccessAPITests(MenuAPITestBase):

    def test_cashier_cannot_create_category(self):
        self.authenticate(self.cashier)
        resp = self.client.post(reverse("menu:category-list"), {"name": "Silog"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_update_category(self):
        cat = self.make_category(name="Silog")
        self.authenticate(self.cashier)
        resp = self.client.patch(
            reverse("menu:category-detail", args=[cat.pk]),
            {"name": "Hijack"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_delete_category(self):
        cat = self.make_category(name="Silog")
        self.authenticate(self.cashier)
        resp = self.client.delete(reverse("menu:category-detail", args=[cat.pk]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create_category(self):
        self.authenticate(self.manager)
        resp = self.client.post(reverse("menu:category-list"), {"name": "Silog"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_blocked(self):
        resp = self.client.post(reverse("menu:category-list"), {"name": "Silog"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_cannot_list(self):
        self.make_category(name="Silog")
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)