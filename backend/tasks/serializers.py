from typing import Any, Optional, cast

from rest_framework import serializers
from .models import Task
from topics.models import Topic


class TaskSerializer(serializers.ModelSerializer):
    topic_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        write_only=True,
    )

    topic = serializers.SerializerMethodField(read_only=True)

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

    def create(self, validated_data: dict[str, Any]) -> Task:
        topic_id: Optional[str] = validated_data.pop("topic_id", None)
        task = Task.objects.create(**validated_data)
        if topic_id is not None:
            setattr(task, "topic_id", topic_id)
            task.save(update_fields=["topic"])
        return task

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        topic_id: Optional[str] = validated_data.pop("topic_id", None)
        task = cast(Task, super().update(instance, validated_data))
        if topic_id is not None:
            setattr(task, "topic_id", topic_id)
            task.save(update_fields=["topic"])
        return task
