import uuid
from django.db import models
from courses.models import Course
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from tasks.models import Task
    from django.db.models.manager import Manager


class Topic(models.Model):
    id: ClassVar[models.UUIDField] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    course: "Course" = models.ForeignKey(
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

    def recalc_progress(self) -> None:
        tasks: "Manager[Task]" = self.tasks  # type: ignore[attr-defined]

        total = tasks.count() - tasks.filter(status="cancelled").count()

        if total == 0:
            self.progress = 0  # type: ignore
            self.save(update_fields=["progress"])
            return

        done = tasks.filter(status="done").count()
        self.progress = int(done / total * 100)  # type: ignore
        self.save(update_fields=["progress"])
