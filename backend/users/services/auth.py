import logging
from typing import Any, cast

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import UserSerializer

logger = logging.getLogger(__name__)

TELEGRAM_MUTABLE_FIELDS = ("username", "first_name", "language", "timezone")


def issue_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    logger.info(
        "JWT tokens issued",
        extra={
            "user_id": user.id,
            "email": getattr(user, "email", None),
            "is_active": user.is_active,
        },
    )
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def build_auth_response(user: User) -> dict[str, Any]:
    return {
        "user": UserSerializer(user).data,
        "tokens": issue_tokens(user),
    }


def get_or_create_telegram_user(data: dict[str, Any]) -> tuple[User, bool]:
    return cast(
        tuple[User, bool],
        User.objects.get_or_create(
            telegram_id=data["telegram_id"],
            defaults=_build_telegram_user_defaults(data),
        ),
    )


def update_telegram_user(user: User, data: dict[str, Any]) -> list[str]:
    updated_fields: list[str] = []

    for field in TELEGRAM_MUTABLE_FIELDS:
        value = data.get(field)
        if value and getattr(user, field) != value:
            setattr(user, field, value)
            updated_fields.append(field)

    if not user.password:
        user.set_unusable_password()
        updated_fields.append("password")

    if updated_fields:
        user.save(update_fields=updated_fields)
        logger.info(
            "Telegram user updated",
            extra={
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "updated_fields": updated_fields,
            },
        )

    return updated_fields


def register_email_user(data: dict[str, Any]) -> User:
    user = User.objects.create_user(**data)
    logger.info(
        "Email user created",
        extra={"user_id": user.id, "email": user.email},
    )
    return user


def authenticate_email_user(request: Request, data: dict[str, Any]) -> User:
    user = authenticate(request=request, email=data["email"], password=data["password"])
    if user is None:
        raise AuthenticationFailed("Неверный email или пароль.")

    auth_user = cast(User, user)
    logger.info(
        "Email login successful",
        extra={"user_id": auth_user.id, "email": auth_user.email},
    )
    return auth_user


def link_email_credentials(user: User, data: dict[str, Any]) -> User:
    email = data["email"]
    existing_user = User.objects.filter(email=email).exclude(pk=user.pk).first()
    if existing_user is not None:
        raise ValidationError({"email": "Этот email уже используется другим пользователем."})

    if user.email and user.email != email:
        raise ValidationError(
            {"email": "К аккаунту уже привязан другой email. Смена email сейчас не поддерживается."}
        )

    updated_fields: list[str] = []
    if user.email != email:
        setattr(user, "email", email)
        setattr(user, "email_verified", False)
        updated_fields.extend(["email", "email_verified"])

    user.set_password(data["password"])
    updated_fields.append("password")
    user.save(update_fields=updated_fields)

    logger.info(
        "Email credentials linked",
        extra={
            "user_id": user.id,
            "email": user.email,
            "telegram_id": user.telegram_id,
        },
    )
    return user


def _build_telegram_user_defaults(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "username": data.get("username"),
        "first_name": data.get("first_name", ""),
        "language": data.get("language", "en"),
        "timezone": data.get("timezone", "UTC"),
        "password": make_password(None),
    }
