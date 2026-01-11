import logging
from typing import cast, Any

from drf_spectacular.utils import extend_schema
from rest_framework import status, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    TelegramLoginSerializer,
    UserSerializer,
    TelegramLoginResponseSerializer,
)

logger = logging.getLogger(__name__)


class TelegramLoginView(APIView):
    """Создание или обновление пользователя по Telegram ID"""

    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _get_tokens_for_user(user: User) -> dict[str, str]:
        """Создаёт JWT-токены для пользователя"""
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

    @staticmethod
    def _update_user_fields(user: User, data: Any) -> list[str]:
        """Обновляет изменившиеся поля пользователя"""
        updated_fields = []
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

        return updated_fields

    @extend_schema(  # type: ignore
        request=TelegramLoginSerializer,
        responses=TelegramLoginResponseSerializer,
        tags=["Users"],
        summary="Telegram login",
        description="Создание или обновление пользователя по Telegram ID",
    )
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

        user, created = User.objects.get_or_create(
            telegram_id=data["telegram_id"],
            defaults={
                "username": data.get("username"),
                "first_name": data.get("first_name", ""),
                "language": data.get("language", "en"),
                "timezone": data.get("timezone", "UTC"),
            },
        )

        if created:
            logger.info(
                "Telegram user created",
                extra={"user_id": user.id, "telegram_id": user.telegram_id},
            )
        else:
            self._update_user_fields(user, data)

        tokens = self._get_tokens_for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
                "created": created,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Получение текущего пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(  # type: ignore
        responses={200: UserSerializer},
        tags=["Users"],
        summary="Текущий пользователь",
    )
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
