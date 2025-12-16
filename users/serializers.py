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
            "username",
            "first_name",
            "language",
            "timezone",
            "created_at",
        )

class TelegramLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = serializers.DictField(child=serializers.CharField())
    created = serializers.BooleanField()