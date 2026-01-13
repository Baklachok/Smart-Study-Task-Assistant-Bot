import logging
from typing import Any, Optional, cast

from django.utils import timezone
from datetime import timezone as dt_timezone, datetime
from rest_framework import serializers
from .models import Task
from topics.models import Topic

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
        ]
        read_only_fields = ["id", "created_at"]

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

        if instance.due_at:
            request = self.context.get("request")
            if request:
                user = request.user
                user_tz = get_user_timezone(user)
                data["due_at"] = instance.due_at.astimezone(user_tz).isoformat()

        return data

    def create(self, validated_data: dict[str, Any]) -> Task:
        topic_id = validated_data.pop("topic_id", None)

        if topic_id is not None:
            validated_data["topic_id"] = topic_id

        task = Task.objects.create(**validated_data)
        return task

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        topic_id: Optional[str] = validated_data.pop("topic_id", None)
        task = cast(Task, super().update(instance, validated_data))
        if topic_id is not None:
            setattr(task, "topic_id", topic_id)
            task.save(update_fields=["topic"])
        return task

    def validate_due_at(self, value: datetime) -> datetime | None:
        if value is None:
            return None

        request = self.context["request"]
        user = request.user

        user_tz = get_user_timezone(user)

        if timezone.is_naive(value):
            value = user_tz.localize(value)

        value_utc = value.astimezone(dt_timezone.utc)

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

        return value_utc
