from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Restaurant, User
from inventory.models import Ingredient, InventoryTransaction
from menu.models import AddOn, Category, MenuItem

from .forms import RecipeForm, RecipeIngredientForm
from .models import Recipe, RecipeIngredient


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class RecipeBase(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.category = Category.objects.create(restaurant_id=self.rid, name="Rice Meals")
        self.menu_item = MenuItem.objects.create(
            restaurant_id=self.rid, category=self.category,
            name="Chicken Adobo", price=Decimal("120"),
        )
        self.addon = AddOn.objects.create(
            restaurant_id=self.rid, name="Extra Rice", price=Decimal("15"),
        )
        self.rice = Ingredient.objects.create(
            restaurant_id=self.rid, name="Rice", unit_of_measure="kg",
            average_unit_cost=Decimal("50"),
        )
        self.chicken = Ingredient.objects.create(
            restaurant_id=self.rid, name="Chicken", unit_of_measure="kg",
            average_unit_cost=Decimal("180"),
        )


class RecipeModelTests(RecipeBase):
    def test_recipe_cost_and_margin(self):
        """FR-071: cost from ingredient weighted-average costs; margin vs price."""
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Adobo Recipe",
        )
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.rice, quantity=Decimal("0.2"))
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.chicken, quantity=Decimal("0.3"))
        self.assertEqual(recipe.cost, Decimal("64"))
        self.assertAlmostEqual(recipe.margin, Decimal("46.67"), places=2)

    def test_get_for_menu_item_and_addon(self):
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, addon=self.addon, name="Rice Recipe",
        )
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.rice, quantity=Decimal("0.15"))
        self.assertEqual(Recipe.get_for(addon=self.addon), recipe)
        self.assertIsNone(Recipe.get_for(menu_item=self.menu_item))

    def test_cross_restaurant_ingredient_rejected(self):
        other = Restaurant.objects.create(name="Other")
        foreign_rice = Ingredient.objects.create(
            restaurant_id=other.pk, name="Rice", unit_of_measure="kg",
        )
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Bad",
        )
        with self.assertRaises(ValidationError):
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=foreign_rice, quantity=Decimal("1"),
            )


class RecipeFormTests(RecipeBase):
    def test_requires_exactly_one_target(self):
        form = RecipeForm(data={"name": "X"}, restaurant_id=self.rid)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_valid_menu_item_recipe(self):
        form = RecipeForm(
            data={"name": "Adobo Recipe", "menu_item": self.menu_item.pk},
            restaurant_id=self.rid,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_ingredient_quantity_positive(self):
        recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Adobo Recipe",
        )
        form = RecipeIngredientForm(
            data={"ingredient": self.rice.pk, "quantity": "0"},
            restaurant_id=self.rid,
        )
        self.assertFalse(form.is_valid())


class RecipeViewTests(RecipeBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)
        self.recipe = Recipe.objects.create(
            restaurant_id=self.rid, menu_item=self.menu_item, name="Adobo Recipe",
        )
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.rice, quantity=Decimal("0.2"))

    def test_list_shows_recipe(self):
        response = self.client.get(reverse("recipes:recipe_list"))
        self.assertContains(response, "Adobo Recipe")

    def test_create_with_line(self):
        response = self.client.post(reverse("recipes:recipe_create"), {
            "name": "Rice Recipe",
            "addon": self.addon.pk,
            "ingredient": self.rice.pk,
            "quantity": "0.15",
        })
        self.assertRedirects(response, reverse("recipes:recipe_detail", args=[Recipe.objects.get(name="Rice Recipe").pk]))
        recipe = Recipe.objects.get(name="Rice Recipe")
        self.assertEqual(recipe.lines.count(), 1)

    def test_kitchen_can_read_recipes(self):
        kitchen = User.objects.create_user(
            email="kitchen@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.KITCHEN,
        )
        self.client.force_login(kitchen)
        response = self.client.get(reverse("recipes:recipe_list"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("recipes:recipe_create"))
        self.assertEqual(response.status_code, 302)

    def test_cashier_blocked(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse("recipes:recipe_list"))
        self.assertEqual(response.status_code, 302)

    def test_delete_removes_recipe(self):
        response = self.client.post(reverse("recipes:recipe_delete", args=[self.recipe.pk]))
        self.assertRedirects(response, reverse("recipes:recipe_list"))
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_duplicate_line_add_is_rejected(self):
        response = self.client.post(
            reverse("recipes:recipe_line_add", args=[self.recipe.pk]),
            {"ingredient": self.rice.pk, "quantity": "0.5"},
        )
        self.assertRedirects(response, reverse("recipes:recipe_detail", args=[self.recipe.pk]))
        self.assertEqual(self.recipe.lines.count(), 1)

    def test_duplicate_ingredient_on_edit_is_rejected(self):
        response = self.client.post(reverse("recipes:recipe_edit", args=[self.recipe.pk]), {
            "name": "Adobo Recipe",
            "menu_item": self.menu_item.pk,
            "ingredient": self.rice.pk,
            "quantity": "0.5",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.recipe.lines.count(), 1)
