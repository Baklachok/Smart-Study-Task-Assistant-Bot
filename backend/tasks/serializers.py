from datetime import timezone as dt_timezone, datetime
import logging
from typing import Any, Optional, cast

from django.utils import timezone
from rest_framework import serializers

from .models import Task
from topics.models import Topic

from users.models import User
from users.utils.timezone import get_user_timezone

logger = logging.getLogger(__name__)


class TaskSerializer(serializers.ModelSerializer):
    topic_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        write_only=True,
    )

    topic = serializers.SerializerMethodField(read_only=True)
    due_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_at",
            "status",
            "priority",
            "topic",
            "topic_id",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["id", "created_at", "completed_at"]

    def get_topic(self, obj: Task) -> Optional[dict[str, str]]:
        topic = cast(Optional[Topic], obj.topic)
        if not topic:
            return None
        return {
            "id": str(topic.id),
            "title": topic.title,
        }

    def to_representation(self, instance: Task) -> dict[str, Any]:
        data = cast(dict[str, Any], super().to_representation(instance))
        data["due_at"] = self._format_due_at(instance)
        return data

    def create(self, validated_data: dict[str, Any]) -> Task:
        self._apply_topic_id(validated_data)

        if validated_data.get("status") == Task.Status.DONE:
            validated_data.setdefault("completed_at", timezone.now())

        return Task.objects.create(**validated_data)

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        topic_id: Optional[str] = validated_data.pop("topic_id", None)
        task = cast(Task, super().update(instance, validated_data))
        if topic_id is not None:
            setattr(task, "topic_id", topic_id)
            task.save(update_fields=["topic"])
        return task

    def _apply_topic_id(self, validated_data: dict[str, Any]) -> None:
        topic_id = validated_data.pop("topic_id", None)
        if topic_id is not None:
            validated_data["topic_id"] = topic_id

    def _get_context_user(self) -> User | None:
        request = self.context.get("request")
        if not request:
            return None
        return cast(User, cast(Any, request).user)

    def _format_due_at(self, instance: Task) -> str | None:
        if not instance.due_at:
            return None

        due_at = cast(datetime, instance.due_at)
        user = self._get_context_user()
        if not user:
            return due_at.isoformat()

        return due_at.astimezone(get_user_timezone(user)).isoformat()

    @staticmethod
    def _normalize_due_at(value: datetime, user: User) -> datetime:
        user_tz = get_user_timezone(user)
        if timezone.is_naive(value):
            return cast(datetime, user_tz.localize(value))
        return value

    def _require_context_user(self) -> User:
        return cast(User, self._get_context_user())

    @staticmethod
    def _validate_due_at_not_in_past(value_utc: datetime, user: User) -> None:
        now_utc = timezone.now()
        if value_utc < now_utc:
            logger.warning(
                "Попытка установить дедлайн в прошлом",
                extra={
                    "user_id": getattr(user, "id", None),
                    "attempted_due_at": value_utc.isoformat(),
                    "now_utc": now_utc.isoformat(),
                },
            )
            raise serializers.ValidationError("Нельзя установить дедлайн в прошлом.")

    def validate_due_at(self, value: datetime) -> datetime | None:
        if value is None:
            return None

        user = self._require_context_user()
        normalized_value = self._normalize_due_at(value, user)
        value_utc = normalized_value.astimezone(dt_timezone.utc)
        self._validate_due_at_not_in_past(value_utc, user)

        return value_utc


class HabitsReportSerializer(serializers.Serializer):
    short_text = serializers.CharField()
    long_text = serializers.CharField()
    metrics = serializers.JSONField()
