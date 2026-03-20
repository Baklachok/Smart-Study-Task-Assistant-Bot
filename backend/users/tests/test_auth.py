from typing import Any, cast

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from users.models import User


class EmailAuthTests(APITestCase):
    register_url = "/api/v1/users/register/"
    login_url = "/api/v1/users/login/"
    link_email_url = "/api/v1/users/link-email/"
    telegram_login_url = "/api/v1/users/telegram-login/"
    me_url = "/api/v1/users/me/"

    @staticmethod
    def _response_data(response: Response) -> dict[str, Any]:
        return cast(dict[str, Any], response.data)

    def test_register_creates_email_user_and_returns_tokens(self) -> None:
        response = self.client.post(
            self.register_url,
            {
                "email": "student@example.com",
                "password": "StrongPass123!",
                "first_name": "Daniil",
            },
            format="json",
        )
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", cast(dict[str, Any], data["tokens"]))
        self.assertEqual(cast(dict[str, Any], data["user"])["email"], "student@example.com")
        self.assertFalse(cast(dict[str, Any], data["user"])["email_verified"])

        user = User.objects.get(email="student@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertIsNone(user.telegram_id)

    def test_login_returns_tokens_for_email_user(self) -> None:
        User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            first_name="Student",
        )

        response = self.client.post(
            self.login_url,
            {"email": "student@example.com", "password": "StrongPass123!"},
            format="json",
        )
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", cast(dict[str, Any], data["tokens"]))
        self.assertEqual(cast(dict[str, Any], data["user"])["email"], "student@example.com")

    def test_login_rejects_invalid_password(self) -> None:
        User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            self.login_url,
            {"email": "student@example.com", "password": "WrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_link_email_allows_email_login_for_existing_telegram_user(self) -> None:
        user = User.objects.create_user(
            telegram_id=123456789,
            username="tg_user",
            first_name="Telegram",
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.link_email_url,
            {"email": "telegram.user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["email"], "telegram.user@example.com")
        self.assertFalse(data["email_verified"])

        user.refresh_from_db()
        self.assertTrue(user.check_password("StrongPass123!"))

        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            self.login_url,
            {"email": "telegram.user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        login_data = self._response_data(login_response)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(cast(dict[str, Any], login_data["user"])["id"], str(user.id))

    def test_link_email_rejects_duplicate_email(self) -> None:
        User.objects.create_user(
            email="taken@example.com",
            password="StrongPass123!",
        )
        telegram_user = User.objects.create_user(telegram_id=987654321)
        self.client.force_authenticate(user=telegram_user)

        response = self.client.post(
            self.link_email_url,
            {"email": "taken@example.com", "password": "StrongPass123!"},
            format="json",
        )
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", data)

    def test_telegram_login_creates_user_with_unusable_password(self) -> None:
        response = self.client.post(
            self.telegram_login_url,
            {
                "telegram_id": 555111222,
                "username": "telegram_user",
                "first_name": "Tg",
            },
            format="json",
        )
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(data["created"])

        user = User.objects.get(telegram_id=555111222)
        self.assertFalse(user.has_usable_password())

    def test_me_includes_email_fields(self) -> None:
        user = User.objects.create_user(
            email="me@example.com",
            password="StrongPass123!",
            first_name="Me",
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.me_url)
        data = self._response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["email"], "me@example.com")
        self.assertIn("email_verified", data)
