from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import User
from .serializers import TelegramLoginSerializer, UserSerializer, TelegramLoginResponseSerializer
from .utils import get_tokens_for_user


@extend_schema(
    request=TelegramLoginSerializer,
    responses=TelegramLoginResponseSerializer,
    tags=["Users"],
    summary="Telegram login",
    description="Создание или обновление пользователя по Telegram ID",
)
class TelegramLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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
            }
        )

        if not created:
            updated = False
            for field in ("username", "first_name", "language", "timezone"):
                value = data.get(field)
                if value and getattr(user, field) != value:
                    setattr(user, field, value)
                    updated = True
            if updated:
                user.save()

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
                "created": created,
            },
            status=status.HTTP_200_OK
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

    def get(self, request):
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK
        )
