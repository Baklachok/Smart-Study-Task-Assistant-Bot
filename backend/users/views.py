import logging
from typing import Any, cast

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .api.schema import (
    EMAIL_LOGIN_SCHEMA,
    EMAIL_REGISTER_SCHEMA,
    LINK_EMAIL_SCHEMA,
    ME_SCHEMA,
    TELEGRAM_LOGIN_SCHEMA,
    TOKEN_REFRESH_SCHEMA,
)
from .models import User
from .serializers import (
    EmailLoginSerializer,
    EmailRegisterSerializer,
    LinkEmailSerializer,
    TelegramLoginSerializer,
    UserSerializer,
)
from .services.auth import (
    authenticate_email_user,
    build_auth_response,
    get_or_create_telegram_user,
    issue_tokens,
    link_email_credentials,
    register_email_user,
    update_telegram_user,
)

logger = logging.getLogger(__name__)


class TelegramLoginView(APIView):
    """Создание или обновление пользователя по Telegram ID."""

    permission_classes = [permissions.AllowAny]

    @TELEGRAM_LOGIN_SCHEMA  # type: ignore[untyped-decorator]
    def post(self, request: Request) -> Response:
        logger.info(
            "Telegram login attempt",
            extra={
                "telegram_id": request.data.get("telegram_id"),
                "username": request.data.get("username"),
                "timezone": request.data.get("timezone"),
            },
        )

        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, created = get_or_create_telegram_user(data)

        if created:
            logger.info(
                "Telegram user created",
                extra={"user_id": user.id, "telegram_id": user.telegram_id},
            )
        else:
            update_telegram_user(user, data)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": issue_tokens(user),
                "created": created,
            },
            status=status.HTTP_200_OK,
        )


class EmailRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @EMAIL_REGISTER_SCHEMA  # type: ignore[untyped-decorator]
    def post(self, request: Request) -> Response:
        serializer = EmailRegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = register_email_user(serializer.validated_data)

        return Response(
            build_auth_response(user),
            status=status.HTTP_201_CREATED,
        )


class EmailLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @EMAIL_LOGIN_SCHEMA  # type: ignore[untyped-decorator]
    def post(self, request: Request) -> Response:
        serializer = EmailLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = authenticate_email_user(request, serializer.validated_data)
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class LinkEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @LINK_EMAIL_SCHEMA  # type: ignore[untyped-decorator]
    def post(self, request: Request) -> Response:
        user = cast(User, request.user)
        serializer = LinkEmailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        linked_user = link_email_credentials(user, serializer.validated_data)
        return Response(UserSerializer(linked_user).data, status=status.HTTP_200_OK)


class MeView(APIView):
    """Получение текущего пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    @ME_SCHEMA  # type: ignore[untyped-decorator]
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        logger.debug(
            "User requested /me",
            extra={"user_id": user.id, "telegram_id": user.telegram_id},
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


class UserTokenRefreshView(TokenRefreshView):  # type: ignore[misc]
    @TOKEN_REFRESH_SCHEMA  # type: ignore[untyped-decorator]
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return cast(Response, super().post(request, *args, **kwargs))
