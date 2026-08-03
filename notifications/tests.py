from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User

from .models import Notification
from .services import Notifier, notify, notify_role


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class NotificationModelTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.kitchen = User.objects.create_user(
            email="kitchen@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.KITCHEN,
        )

    def test_notify_creates_role_addressed_entries(self):
        created = notify(
            self.rid, Notification.Type.NEW_ORDER, "New order #0001",
            roles=(User.Role.KITCHEN,), link="/orders/1/",
        )
        self.assertEqual(len(created), 1)
        entry = Notification.objects.get(restaurant_id=self.rid)
        self.assertEqual(entry.target_role, User.Role.KITCHEN)
        self.assertEqual(entry.link, "/orders/1/")

    def test_for_user_matches_role_and_direct(self):
        notify(self.rid, Notification.Type.NEW_ORDER, "To kitchen", roles=(User.Role.KITCHEN,))
        notify(self.rid, Notification.Type.LOW_STOCK, "To owner", user=self.owner)
        self.assertEqual(Notification.for_user(self.kitchen).count(), 1)
        self.assertEqual(Notification.for_user(self.owner).count(), 1)
        self.assertEqual(Notification.unread_count(self.kitchen), 1)
        self.assertEqual(Notification.unread_count(self.owner), 1)

    def test_mark_read(self):
        notification = notify(self.rid, Notification.Type.LOW_STOCK, "Low stock", user=self.owner)[0]
        notification.mark_read()
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
        self.assertEqual(Notification.unread_count(self.owner), 0)

    def test_mark_all_read_view(self):
        notify(self.rid, Notification.Type.LOW_STOCK, "A", user=self.owner)
        notify(self.rid, Notification.Type.LOW_STOCK, "B", user=self.owner)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("notifications:notification_mark_all_read"))
        self.assertRedirects(response, reverse("notifications:notification_list"))
        self.assertEqual(Notification.unread_count(self.owner), 0)

    def test_purge_old(self):
        """FR-153: notifications older than 90 days are purged."""
        notify(self.rid, Notification.Type.LOW_STOCK, "Old", user=self.owner)
        Notification.objects.filter(restaurant_id=self.rid).update(
            created_at=timezone.now() - timezone.timedelta(days=91),
        )
        notify(self.rid, Notification.Type.LOW_STOCK, "New", user=self.owner)
        deleted = Notification.purge_old()
        self.assertEqual(deleted, 1)
        self.assertEqual(Notification.objects.filter(restaurant_id=self.rid).count(), 1)


class NotifierTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.manager = User.objects.create_user(
            email="manager@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )

    def test_order_placed_goes_to_kitchen(self):
        order = type("Order", (), {
            "restaurant_id": self.rid, "pk": 1, "order_number": "#0001",
            "total": 100, "order_type": "DINE_IN",
            "get_order_type_display": lambda self: "Dine-in",
        })()
        Notifier().order_placed(order)
        entry = Notification.objects.get(type=Notification.Type.NEW_ORDER)
        self.assertEqual(entry.target_role, User.Role.KITCHEN)

    def test_order_cancelled_goes_to_kitchen_and_manager(self):
        order = type("Order", (), {
            "restaurant_id": self.rid, "pk": 1, "order_number": "#0001",
            "cancel_reason": "out of stock",
        })()
        Notifier().order_cancelled(order)
        self.assertEqual(Notification.objects.filter(type=Notification.Type.ORDER_CANCELLED).count(), 2)

    def test_large_discount_goes_to_owner_and_manager(self):
        order = type("Order", (), {
            "restaurant_id": self.rid, "pk": 1, "order_number": "#0001",
            "discount_amount": 50, "discount_type": "MANUAL",
            "discount_needs_approval": True,
            "get_discount_type_display": lambda self: "Manual",
        })()
        Notifier().large_discount(order, self.owner)
        self.assertEqual(Notification.objects.filter(type=Notification.Type.LARGE_DISCOUNT).count(), 2)
