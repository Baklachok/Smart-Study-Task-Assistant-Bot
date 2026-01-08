import uuid
from typing import ClassVar

from django.db import models

from topics.models import Topic
from users.models import User


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE = "done", "Done"
        CANCELED = "canceled", "Canceled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id: ClassVar[models.UUIDField] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    user: ClassVar[models.ForeignKey] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks"
    )

    title: ClassVar[models.CharField] = models.CharField(max_length=255)

    description: ClassVar[models.TextField] = models.TextField(blank=True)

    due_at: ClassVar[models.DateTimeField] = models.DateTimeField(null=True, blank=True)

    status: ClassVar[models.CharField] = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )

    priority: ClassVar[models.CharField] = models.CharField(
        max_length=6, choices=Priority.choices, default=Priority.MEDIUM
    )

    topic: ClassVar[models.ForeignKey] = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )

    created_at: ClassVar[models.DateTimeField] = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"
