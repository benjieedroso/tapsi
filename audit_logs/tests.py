from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Restaurant, User

from .models import AuditLog
from .services import log, log_denied


def _make_owner():
    restaurant = Restaurant.objects.create(name="TAPSI Test")
    user = User.objects.create_user(
        email="owner@test.com", password="SecurePass123",
        restaurant=restaurant, role=User.Role.OWNER,
    )
    return restaurant, user


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id

    def test_log_captures_actor_role_and_restaurant(self):
        """FR-161: timestamp, user, role, restaurant captured."""
        entry = log(
            actor=self.owner, action="CREATE", entity="supplier", entity_id=7,
            before={}, after={"name": "Depot"},
        )
        self.assertEqual(entry.restaurant_id, self.rid)
        self.assertEqual(entry.actor_role, User.Role.OWNER)
        self.assertEqual(entry.action, "CREATE")
        self.assertEqual(entry.entity, "supplier")
        self.assertEqual(entry.after, {"name": "Depot"})

    def test_log_without_actor(self):
        entry = log(action="SYSTEM", entity="daily_closing", entity_id=1)
        self.assertIsNone(entry.actor)
        self.assertIsNone(entry.restaurant_id)

    def test_entries_are_append_only(self):
        """FR-162: no API to modify or delete entries."""
        entry = log(actor=self.owner, action="UPDATE", entity="expense", entity_id=1)
        with self.assertRaises(NotImplementedError):
            entry.delete()

    def test_log_denied(self):
        request = type("Request", (), {
            "user": self.owner, "META": {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "test-agent"},
        })()
        entry = log_denied(request, "expenses:approve")
        self.assertEqual(entry.action, "PERMISSION_DENIED")
        self.assertEqual(entry.ip_address, "127.0.0.1")
        self.assertEqual(entry.user_agent, "test-agent")

    def test_scoped_to_restaurant(self):
        other = Restaurant.objects.create(name="Other")
        log(actor=self.owner, action="CREATE", entity="x")
        entry = AuditLog.objects.create(
            restaurant_id=other.pk, action="CREATE", entity="x",
        )
        scoped = list(AuditLog.scoped(self.rid))
        self.assertEqual(len(scoped), 1)
        self.assertNotIn(entry, scoped)


class AuditLogViewTests(TestCase):
    def setUp(self):
        self.restaurant, self.owner = _make_owner()
        self.rid = self.owner.restaurant_id
        self.manager = User.objects.create_user(
            email="manager@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        log(actor=self.owner, action="DAY_CLOSE", entity="daily_closing", entity_id=1)
        log(actor=self.manager, action="UPDATE", entity="attendance", entity_id=3)

    def test_owner_sees_restaurant_logs(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("audit_logs:audit_log_list"))
        self.assertContains(response, "DAY_CLOSE")
        self.assertContains(response, "UPDATE")

    def test_manager_can_read(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("audit_logs:audit_log_list"))
        self.assertEqual(response.status_code, 200)

    def test_cashier_denied(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse("audit_logs:audit_log_list"))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_action(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("audit_logs:audit_log_list"), {"action": "DAY_CLOSE"})
        self.assertContains(response, "DAY_CLOSE")
        self.assertNotContains(response, 'badge badge-secondary">UPDATE')
