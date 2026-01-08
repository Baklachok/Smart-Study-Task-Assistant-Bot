import uuid
from typing import ClassVar

from django.db import models
from courses.models import Course


class Topic(models.Model):
    id: ClassVar[models.UUIDField] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    course: ClassVar[models.ForeignKey] = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="topics",
    )

    title: ClassVar[models.CharField] = models.CharField(max_length=255)

    progress: ClassVar[models.PositiveSmallIntegerField] = (
        models.PositiveSmallIntegerField(default=0)
    )

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.progress}%)"
