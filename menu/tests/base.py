from rest_framework.test import APITestCase, APIClient

from accounts.models import Restaurant, User
from menu.models import Category, MenuItem, AddOn, MenuItemAddOn


class MenuAPITestBase(APITestCase):
    """Shared fixtures for all menu DRF API tests."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Testaurant")
        self.other_restaurant = Restaurant.objects.create(name="Other")

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
        self.other_owner = User.objects.create_user(
            email="other@test.com", password="testpass1234",
            first_name="Other", last_name="Owner",
            restaurant=self.other_restaurant, role=User.Role.OWNER,
        )
        self.client = APIClient()

    def authenticate(self, user):
        """Skip JWT — test the view logic in isolation."""
        self.client.force_authenticate(user=user)

    # ── Fixture helpers ──────────────────────────────────────────────

    def make_category(self, name="Silog", restaurant=None, **kwargs):
        return Category.objects.create(
            restaurant_id=(restaurant or self.restaurant).pk,
            name=name, **kwargs,
        )

    def make_menu_item(self, name="Tapsilog", price="75.00", category=None,
                       restaurant=None, **kwargs):
        from decimal import Decimal
        return MenuItem.objects.create(
            restaurant_id=(restaurant or self.restaurant).pk,
            name=name, price=Decimal(price), category=category, **kwargs,
        )

    def make_addon(self, name="Extra Rice", price="15.00", restaurant=None, **kwargs):
        from decimal import Decimal
        return AddOn.objects.create(
            restaurant_id=(restaurant or self.restaurant).pk,
            name=name, price=Decimal(price), **kwargs,
        )