from django.core import mail
from django.test import TestCase
from django.utils import timezone
import json
from django.urls import reverse

from .forms import RegistrationForm
from .models import AuthenticationAudit, RefreshToken, User
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
