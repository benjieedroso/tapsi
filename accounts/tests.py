from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .forms import RegistrationForm
from .models import AuthenticationAudit, User


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
