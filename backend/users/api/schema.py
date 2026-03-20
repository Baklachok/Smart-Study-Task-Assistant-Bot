from drf_spectacular.utils import extend_schema

from users.serializers import (
    AuthResponseSerializer,
    EmailLoginSerializer,
    EmailRegisterSerializer,
    LinkEmailSerializer,
    TelegramLoginResponseSerializer,
    TelegramLoginSerializer,
    UserSerializer,
)

TELEGRAM_LOGIN_SCHEMA = extend_schema(
    request=TelegramLoginSerializer,
    responses=TelegramLoginResponseSerializer,
    tags=["Users"],
    summary="Telegram login",
    description="Создание или обновление пользователя по Telegram ID",
)

EMAIL_REGISTER_SCHEMA = extend_schema(
    request=EmailRegisterSerializer,
    responses={201: AuthResponseSerializer},
    tags=["Users"],
    summary="Регистрация по email",
    description="Создает пользователя по email/password и сразу возвращает JWT-токены.",
)

EMAIL_LOGIN_SCHEMA = extend_schema(
    request=EmailLoginSerializer,
    responses={200: AuthResponseSerializer},
    tags=["Users"],
    summary="Логин по email",
    description="Аутентифицирует пользователя по email/password и возвращает JWT-токены.",
)

LINK_EMAIL_SCHEMA = extend_schema(
    request=LinkEmailSerializer,
    responses={200: UserSerializer},
    tags=["Users"],
    summary="Привязать email и пароль",
    description="Привязывает email/password к текущему авторизованному пользователю.",
)

ME_SCHEMA = extend_schema(
    responses={200: UserSerializer},
    tags=["Users"],
    summary="Текущий пользователь",
)

TOKEN_REFRESH_SCHEMA = extend_schema(
    tags=["Users"],
    summary="Обновить access token",
    description="Обновляет access token по refresh token.",
)
