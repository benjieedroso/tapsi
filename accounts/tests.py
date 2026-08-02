from django.core import mail
from django.test import TestCase
from django.utils import timezone
import json
from django.urls import reverse

from .forms import RegistrationForm
from .models import AuthenticationAudit, RefreshToken, StaffAudit, User
from .services import decode_jwt


class RegistrationFormTests(TestCase):
    def test_registration_creates_an_owner_and_restaurant(self):
        form = RegistrationForm(data={
            "restaurant_name": "Benjie's Tapsilogan",
            "first_name": "Benjie",
            "last_name": "Edroso",
            "email": "owner@example.com",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
        })

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertEqual(user.restaurant.name, "Benjie's Tapsilogan")


class StaffAccessTests(TestCase):
    def setUp(self):
        self.owner = RegistrationForm(data={
            "restaurant_name": "TAPSI Test",
            "first_name": "Owner",
            "last_name": "",
            "email": "owner@test.com",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
        })
        self.assertTrue(self.owner.is_valid(), self.owner.errors)
        self.owner = self.owner.save()

    def test_cashier_cannot_open_staff_management(self):
        cashier = User.objects.create_user(
            email="cashier@test.com", password="SecurePass123", restaurant=self.owner.restaurant,
            role=User.Role.CASHIER,
        )
        self.client.force_login(cashier)

        response = self.client.get(reverse("accounts:staff_list"))

        self.assertEqual(response.status_code, 302)

    def test_owner_can_create_staff_account_with_email_as_username(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("accounts:create_staff"), {
            "first_name": "Ana",
            "last_name": "Smith",
            "email": "ana@example.com",
            "phone": "09274928611",
            "role": User.Role.MANAGER,
            "temporary_password": "SecurePass123",
        })

        self.assertRedirects(response, reverse("accounts:staff_list"))
        member = User.objects.get(email="ana@example.com")
        self.assertEqual(member.username, "ana@example.com")
        self.assertEqual(member.restaurant, self.owner.restaurant)
        self.assertTrue(member.must_change_password)


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="SecurePass123", role=User.Role.OWNER,
        )

    def test_five_failed_logins_lock_the_account_and_are_audited(self):
        for _ in range(5):
            response = self.client.post(reverse("accounts:login"), {
                "email": self.user.email, "password": "WrongPass123",
            })
            self.assertEqual(response.status_code, 400)

        self.user.refresh_from_db()
        self.assertGreater(self.user.locked_until, timezone.now())
        self.assertEqual(AuthenticationAudit.objects.filter(
            user=self.user, action=AuthenticationAudit.Action.LOGIN_FAILURE,
        ).count(), 5)
        self.assertTrue(AuthenticationAudit.objects.filter(
            user=self.user, action=AuthenticationAudit.Action.ACCOUNT_LOCKED,
        ).exists())

    def test_email_change_requires_a_confirmation_link(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:request_email_change"), {
            "email": "new-owner@example.com",
        })

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "owner@example.com")
        self.assertEqual(self.user.pending_email, "new-owner@example.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_link_opens_the_new_password_form(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": self.user.email})

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = mail.outbox[0].body.splitlines()[3]
        response = self.client.get(reset_url, follow=True)

        self.assertContains(response, "Choose a new password")
        self.assertContains(response, "New password")

    def test_successful_login_resets_failed_attempts_and_is_audited(self):
        self.user.failed_login_count = 3
        self.user.save(update_fields=["failed_login_count"])

        response = self.client.post(reverse("accounts:login"), {
            "email": self.user.email, "password": "SecurePass123",
        })

        self.assertRedirects(response, reverse("dashboard"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_count, 0)
        self.assertTrue(AuthenticationAudit.objects.filter(
            user=self.user, action=AuthenticationAudit.Action.LOGIN_SUCCESS,
        ).exists())

    def test_password_change_requires_current_password_and_audits_success(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:change_password"), {
            "old_password": "SecurePass123",
            "new_password1": "NewSecurePass123",
            "new_password2": "NewSecurePass123",
        })

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePass123"))
        self.assertTrue(AuthenticationAudit.objects.filter(
            user=self.user, action=AuthenticationAudit.Action.PASSWORD_CHANGED,
        ).exists())

    def test_profile_update_and_logout_are_recorded(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Benjie", "last_name": "Edroso", "phone": "09171234567",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Benjie Edroso")

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(AuthenticationAudit.objects.filter(
            user=self.user, action=AuthenticationAudit.Action.LOGOUT,
        ).exists())

    def test_jwt_login_issues_expected_token_pair(self):
        response = self.client.post(reverse("accounts:api_token"), data=json.dumps({
            "email": self.user.email, "password": "SecurePass123",
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertEqual(tokens["token_type"], "Bearer")
        self.assertEqual(tokens["expires_in"], 900)
        self.assertEqual(decode_jwt(tokens["access"], "access")["sub"], str(self.user.pk))
        self.assertEqual(decode_jwt(tokens["refresh"], "refresh")["sub"], str(self.user.pk))
        self.assertEqual(RefreshToken.objects.filter(user=self.user, revoked_at__isnull=True).count(), 1)

    def test_jwt_refresh_rotation_and_logout_blacklist(self):
        login_response = self.client.post(reverse("accounts:api_token"), data=json.dumps({
            "email": self.user.email, "password": "SecurePass123",
        }), content_type="application/json")
        original_refresh = login_response.json()["refresh"]

        refresh_response = self.client.post(reverse("accounts:api_token_refresh"), data=json.dumps({
            "refresh": original_refresh,
        }), content_type="application/json")
        self.assertEqual(refresh_response.status_code, 200)
        rotated_refresh = refresh_response.json()["refresh"]
        self.assertNotEqual(rotated_refresh, original_refresh)
        self.assertEqual(self.client.post(reverse("accounts:api_token_refresh"), data=json.dumps({
            "refresh": original_refresh,
        }), content_type="application/json").status_code, 401)

        self.assertEqual(self.client.post(reverse("accounts:api_token_logout"), data=json.dumps({
            "refresh": rotated_refresh,
        }), content_type="application/json").status_code, 204)
        self.assertEqual(self.client.post(reverse("accounts:api_token_refresh"), data=json.dumps({
            "refresh": rotated_refresh,
        }), content_type="application/json").status_code, 401)


# ── Module 2: Restaurant & User Management Tests ──


class Module2TestBase(TestCase):
    """Shared setUp for Module 2 tests: creates an owner + restaurant + staff."""
    def setUp(self):
        form = RegistrationForm(data={
            "restaurant_name": "Tapsi Lahat",
            "first_name": "Maria",
            "last_name": "Santos",
            "email": "maria@tapsi.test",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.owner = form.save()
        self.restaurant = self.owner.restaurant

        self.cashier = User.objects.create_user(
            email="cashier@tapsi.test", password="SecurePass123",
            first_name="Juan", last_name="Dela Cruz",
            restaurant=self.restaurant, role=User.Role.CASHIER,
        )
        self.kitchen = User.objects.create_user(
            email="kitchen@tapsi.test", password="SecurePass123",
            first_name="Pedro", last_name="Garcia",
            restaurant=self.restaurant, role=User.Role.KITCHEN,
        )


class RestaurantSettingsTests(Module2TestBase):
    def test_owner_can_view_settings(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("accounts:restaurant_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tapsi Lahat")

    def test_manager_cannot_view_settings(self):
        manager = User.objects.create_user(
            email="manager@tapsi.test", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        self.client.force_login(manager)
        response = self.client.get(reverse("accounts:restaurant_settings"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_owner_can_update_settings(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:restaurant_settings"), {
            "name": "Tapsi Lahat Updated",
            "address": "123 Rizal Ave, Manila",
            "contact_number": "09171234567",
            "tin": "123-456-789-000",
            "receipt_footer": "Maraming salamat po!",
            "is_vat_registered": "on",
        })
        self.assertRedirects(response, reverse("accounts:restaurant_settings"))
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, "Tapsi Lahat Updated")
        self.assertEqual(self.restaurant.tin, "123-456-789-000")
        self.assertTrue(self.restaurant.is_vat_registered)


class StaffRoleChangeTests(Module2TestBase):
    def test_owner_can_change_staff_role(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "change_role",
            "user_id": self.cashier.pk,
            "new_role": User.Role.KITCHEN,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.cashier.refresh_from_db()
        self.assertEqual(self.cashier.role, User.Role.KITCHEN)

    def test_role_change_creates_audit_log(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("accounts:staff_list"), {
            "action": "change_role",
            "user_id": self.cashier.pk,
            "new_role": User.Role.MANAGER,
        })
        audit = StaffAudit.objects.get(target=self.cashier, action=StaffAudit.Action.ROLE_CHANGED)
        self.assertEqual(audit.detail["old_role"], User.Role.CASHIER)
        self.assertEqual(audit.detail["new_role"], User.Role.MANAGER)
        self.assertEqual(audit.actor, self.owner)

    def test_manager_cannot_change_role(self):
        manager = User.objects.create_user(
            email="manager@tapsi.test", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.MANAGER,
        )
        self.client.force_login(manager)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "change_role",
            "user_id": self.cashier.pk,
            "new_role": User.Role.KITCHEN,
        })
        # Manager's POST is ignored (view only processes actions for Owners); returns staff list
        self.assertEqual(response.status_code, 200)
        self.cashier.refresh_from_db()
        self.assertEqual(self.cashier.role, User.Role.CASHIER)


class StaffDeactivationTests(Module2TestBase):
    def test_owner_can_deactivate_staff(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "deactivate",
            "user_id": self.cashier.pk,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.cashier.refresh_from_db()
        self.assertFalse(self.cashier.is_active)

    def test_deactivation_creates_audit_log(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("accounts:staff_list"), {
            "action": "deactivate",
            "user_id": self.cashier.pk,
        })
        self.assertTrue(StaffAudit.objects.filter(
            target=self.cashier, action=StaffAudit.Action.DEACTIVATED,
        ).exists())

    def test_owner_can_reactivate_staff(self):
        self.cashier.is_active = False
        self.cashier.save(update_fields=["is_active"])
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "activate",
            "user_id": self.cashier.pk,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.cashier.refresh_from_db()
        self.assertTrue(self.cashier.is_active)

    def test_reactivation_creates_audit_log(self):
        self.cashier.is_active = False
        self.cashier.save(update_fields=["is_active"])
        self.client.force_login(self.owner)
        self.client.post(reverse("accounts:staff_list"), {
            "action": "activate",
            "user_id": self.cashier.pk,
        })
        self.assertTrue(StaffAudit.objects.filter(
            target=self.cashier, action=StaffAudit.Action.ACTIVATED,
        ).exists())


class LastOwnerProtectionTests(Module2TestBase):
    def test_cannot_deactivate_last_active_owner(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "deactivate",
            "user_id": self.owner.pk,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_can_deactivate_owner_when_two_exist(self):
        second_owner = User.objects.create_user(
            email="owner2@tapsi.test", password="SecurePass123",
            restaurant=self.restaurant, role=User.Role.OWNER,
        )
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_list"), {
            "action": "deactivate",
            "user_id": second_owner.pk,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        second_owner.refresh_from_db()
        self.assertFalse(second_owner.is_active)


class SoftDeleteTests(Module2TestBase):
    def test_user_soft_delete_sets_fields(self):
        from django.utils import timezone as tz
        self.cashier.soft_delete()
        self.cashier.refresh_from_db()
        self.assertTrue(self.cashier.is_deleted)
        self.assertIsNotNone(self.cashier.deleted_at)
        self.assertFalse(self.cashier.is_active)

    def test_soft_deleted_user_excluded_from_default_manager(self):
        self.cashier.soft_delete()
        self.assertFalse(User.objects.filter(pk=self.cashier.pk).exists())


class StaffEditTests(Module2TestBase):
    def test_owner_can_edit_staff(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_edit", args=[self.cashier.pk]), {
            "first_name": "Juanito",
            "last_name": "Dela Cruz",
            "phone": "09171234567",
            "role": User.Role.CASHIER,
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.cashier.refresh_from_db()
        self.assertEqual(self.cashier.first_name, "Juanito")
        self.assertEqual(self.cashier.phone, "09171234567")

    def test_edit_creates_audit_log(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("accounts:staff_edit", args=[self.cashier.pk]), {
            "first_name": "Juanito",
            "last_name": "Dela Cruz",
            "phone": "09171234567",
            "role": User.Role.CASHIER,
        })
        audit = StaffAudit.objects.get(target=self.cashier, action=StaffAudit.Action.PROFILE_UPDATED)
        self.assertIn("changes", audit.detail)

    def test_cannot_assign_owner_role_via_edit(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_edit", args=[self.cashier.pk]), {
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "phone": "",
            "role": User.Role.OWNER,
        })
        self.assertEqual(response.status_code, 200)
        self.cashier.refresh_from_db()
        self.assertEqual(self.cashier.role, User.Role.CASHIER)


class StaffPasswordResetTests(Module2TestBase):
    def test_owner_can_reset_staff_password(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("accounts:staff_reset_password", args=[self.cashier.pk]), {
            "new_password": "NewSecurePass456",
        })
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.cashier.refresh_from_db()
        self.assertTrue(self.cashier.check_password("NewSecurePass456"))
        self.assertTrue(self.cashier.must_change_password)

    def test_password_reset_creates_audit_log(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("accounts:staff_reset_password", args=[self.cashier.pk]), {
            "new_password": "NewSecurePass456",
        })
        self.assertTrue(StaffAudit.objects.filter(
            target=self.cashier, action=StaffAudit.Action.PASSWORD_RESET,
        ).exists())
