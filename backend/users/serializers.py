from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class TelegramLoginSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, default="en")
    timezone = serializers.CharField(required=False, default="UTC")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "telegram_id",
            "email",
            "email_verified",
            "username",
            "first_name",
            "language",
            "timezone",
            "created_at",
        )


class AuthTokensSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = AuthTokensSerializer()


class TelegramLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = AuthTokensSerializer()
    created = serializers.BooleanField()


class EmailValidationMixin(serializers.Serializer):
    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class EmailRegisterSerializer(EmailValidationMixin, serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        email = super().validate_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return email

    def validate_password(self, value: str) -> str:
        validate_password(value, user=None)
        return value


class EmailLoginSerializer(EmailValidationMixin, serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LinkEmailSerializer(EmailValidationMixin, serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value: str) -> str:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        validate_password(value, user=user)
        return value
