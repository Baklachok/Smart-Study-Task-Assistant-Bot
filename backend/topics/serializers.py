from rest_framework import serializers
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Topic
        fields = ("id", "course", "course_name", "title", "progress")

    def validate_progress(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Progress must be between 0 and 100")
        return value
