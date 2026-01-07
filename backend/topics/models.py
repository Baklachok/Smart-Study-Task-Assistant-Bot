import uuid
from django.db import models
from courses.models import Course


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    title = models.CharField(max_length=255)
    progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.progress}%)"
