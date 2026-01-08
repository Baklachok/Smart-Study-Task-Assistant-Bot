import logging
from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    TelegramLoginSerializer,
    UserSerializer,
    TelegramLoginResponseSerializer,
)


logger = logging.getLogger(__name__)


@extend_schema(
    request=TelegramLoginSerializer,
    responses=TelegramLoginResponseSerializer,
    tags=["Users"],
    summary="Telegram login",
    description="Создание или обновление пользователя по Telegram ID",
)
class TelegramLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_tokens_for_user(self, user: User) -> dict[str, str]:
        logger.info(
            "JWT tokens issued",
            extra={
                "user_id": user.id,
                "email": getattr(user, "email", None),
                "is_active": user.is_active,
            },
        )

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def post(self, request: Request) -> Response:
        logger.info(
            "Telegram login attempt",
            extra={
                "telegram_id": request.data.get("telegram_id"),
                "username": request.data.get("username"),
            },
        )

        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, created = User.objects.get_or_create(
            telegram_id=data["telegram_id"],
            defaults={
                "username": data.get("username"),
                "first_name": data.get("first_name", ""),
                "language": data.get("language", "en"),
                "timezone": data.get("timezone", "UTC"),
            },
        )

        updated_fields: list[str] = []

        if not created:
            for field in ("username", "first_name", "language", "timezone"):
                value = data.get(field)
                if value and getattr(user, field) != value:
                    setattr(user, field, value)
                    updated_fields.append(field)

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

        if created:
            logger.info(
                "Telegram user created",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                },
            )

        tokens = self._get_tokens_for_user(user)

        logger.info(
            "JWT tokens issued for Telegram user",
            extra={
                "user_id": user.id,
                "telegram_id": user.telegram_id,
            },
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
                "created": created,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    responses={200: UserSerializer},
    tags=["Users"],
    summary="Текущий пользователь",
)
class MeView(APIView):
    """
    GET /api/v1/users/me/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        logger.debug(
            "User requested /me",
            extra={
                "user_id": user.id,
                "telegram_id": user.telegram_id,
            },
        )

        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )
