from datetime import timedelta

import jwt
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Restaurant, User


class JWTAuthFlowTests(APITestCase):
    """End-to-end JWT: real login, real token, real protected request."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Testaurant")
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass1234",
            first_name="Own", last_name="Er",
            restaurant=self.restaurant, role=User.Role.OWNER,
        )

    # ── Login ────────────────────────────────────────────────────────

    def test_login_returns_access_and_refresh_tokens(self):
        resp = self.client.post("/api/v1/auth/token/", {
            "email": "owner@test.com", "password": "testpass1234",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_with_wrong_password_fails(self):
        resp = self.client.post("/api/v1/auth/token/", {
            "email": "owner@test.com", "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_unknown_email_fails(self):
        resp = self.client.post("/api/v1/auth/token/", {
            "email": "nobody@test.com", "password": "testpass1234",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Token contents ───────────────────────────────────────────────

    def test_access_token_contains_custom_claims(self):
        resp = self.client.post("/api/v1/auth/token/", {
            "email": "owner@test.com", "password": "testpass1234",
        })
        token = resp.data["access"]
        decoded = jwt.decode(token, options={"verify_signature": False})

        self.assertEqual(decoded["restaurant_id"], self.restaurant.pk)
        self.assertEqual(decoded["role"], User.Role.OWNER)
        self.assertEqual(decoded["user_id"], self.owner.pk)

    # ── Protected requests ───────────────────────────────────────────

    def test_real_token_unlocks_protected_endpoint(self):
        login = self.client.post("/api/v1/auth/token/", {
            "email": "owner@test.com", "password": "testpass1234",
        })
        token = login.data["access"]

        # Fresh client, no force_authenticate — use the real token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_missing_token_blocked(self):
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_garbage_token_blocked(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not.a.real.token")
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_blocked(self):
        """Hand-craft an expired token using the real signing key."""
        now = __import__("datetime").datetime.utcnow()
        expired_payload = {
            "token_type": "access",
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "user_id": self.owner.pk,
            "restaurant_id": self.restaurant.pk,
            "role": User.Role.OWNER,
        }
        token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(reverse("menu:category-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Refresh flow ─────────────────────────────────────────────────

    def test_refresh_token_returns_new_access(self):
        login = self.client.post("/api/v1/auth/token/", {
            "email": "owner@test.com", "password": "testpass1234",
        })
        refresh = login.data["refresh"]

        resp = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    # ── Cross-tenant claim integrity ─────────────────────────────────

    def test_token_claim_scopes_to_correct_restaurant(self):
        """A user from restaurant A must be scoped to A, not B."""
        other_restaurant = Restaurant.objects.create(name="Other")
        other_owner = User.objects.create_user(
            email="other@test.com", password="testpass1234",
            first_name="Other", last_name="Owner",
            restaurant=other_restaurant, role=User.Role.OWNER,
        )
        login = self.client.post("/api/v1/auth/token/", {
            "email": "other@test.com", "password": "testpass1234",
        })
        token = login.data["access"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(decoded["restaurant_id"], other_restaurant.pk)
        self.assertNotEqual(decoded["restaurant_id"], self.restaurant.pk)