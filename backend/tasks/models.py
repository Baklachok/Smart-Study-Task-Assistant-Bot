import uuid
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    priority = models.CharField(
        max_length=6, choices=Priority.choices, default=Priority.MEDIUM
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"
