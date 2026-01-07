from rest_framework import serializers
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ("id", "course", "title", "progress")

    def validate_progress(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Progress must be between 0 and 100")
        return value
