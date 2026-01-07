from rest_framework import serializers
from .models import Task


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

    def get_topic(self, obj):
        if not obj.topic:
            return None
        return {
            "id": obj.topic.id,
            "title": obj.topic.title,
        }

    def create(self, validated_data):
        topic_id = validated_data.pop("topic_id", None)
        task = Task.objects.create(**validated_data)
        if topic_id:
            task.topic_id = topic_id
            task.save(update_fields=["topic"])
        return task

    def update(self, instance, validated_data):
        topic_id = validated_data.pop("topic_id", None)
        task = super().update(instance, validated_data)
        if topic_id is not None:
            task.topic_id = topic_id
            task.save(update_fields=["topic"])
        return task
