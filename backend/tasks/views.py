import logging
from datetime import timedelta
from typing import Any, cast

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Task
from .permissions import IsOwner
from .serializers import TaskSerializer
from users.models import User

from .services.reminders import create_default_reminders

logger = logging.getLogger(__name__)


def log_task_action(
    action: str,
    task: Task,
    user_id: int | str,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    """
    Универсальный логгер для действий с задачами.
    action: created/updated/deleted
    """
    extra = {
        "task_id": task.id,
        "user_id": user_id,
        "topic_id": getattr(task, "topic_id", None),
    }
    if extra_fields:
        extra.update(extra_fields)
    logger.info(f"Task {action}", extra=extra)


class TaskListCreateView(generics.ListCreateAPIView):
    """Список задач и создание новой задачи"""

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_user(self) -> User:
        return cast(User, self.request.user)

    def get_queryset(self) -> QuerySet[Any]:
        user = self.get_user()
        queryset = Task.objects.filter(user=user)

        return self._apply_filters(queryset)

    def _apply_filters(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        """Применяет фильтры по дате и теме"""
        user = self.get_user()
        filter_by = self.request.query_params.get("filter")
        topic_id = self.request.query_params.get("topic")
        now = timezone.now()

        logger.debug(
            "Tasks list requested",
            extra={"user_id": user.id, "filter": filter_by, "topic_id": topic_id},
        )

        # Фильтры по времени
        if filter_by == "today":
            queryset = queryset.filter(due_at__date=now.date())
        elif filter_by == "week":
            end_week = now + timedelta(days=7)
            queryset = queryset.filter(
                due_at__date__range=(now.date(), end_week.date())
            )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        user = self.get_user()
        task = serializer.save(user=user)

        create_default_reminders(task)

        log_task_action(
            "created",
            task,
            user.id,
            extra_fields={
                "title": task.title,
                "due_at": task.due_at,
                "priority": task.priority,
            },
        )


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, обновление и удаление задачи"""

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Task.objects.all()

    def get_user(self) -> User:
        return cast(User, self.request.user)

    def retrieve(
        self, request: Request, *args: Any, **kwargs: dict[str, Any]
    ) -> Response:
        task = self.get_object()
        user = self.get_user()
        logger.debug("Task retrieved", extra={"task_id": task.id, "user_id": user.id})
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer: BaseSerializer) -> None:
        task = self.get_object()
        old_data = {
            field: getattr(task, field) for field in serializer.validated_data.keys()
        }

        updated_task = serializer.save()

        changed_fields = {
            field: {"old": old_data[field], "new": getattr(updated_task, field)}
            for field in old_data
            if old_data[field] != getattr(updated_task, field)
        }

        if "due_at" in changed_fields:
            updated_task.reminders.all().delete()
            create_default_reminders(updated_task)

        log_task_action(
            "updated",
            updated_task,
            updated_task.user.id,
            extra_fields={"changed_fields": changed_fields},
        )

    def perform_destroy(self, instance: Task) -> None:
        log_task_action(
            "deleted",
            instance,
            instance.user.id,  # type: ignore
            extra_fields={"title": instance.title},
        )
        instance.delete()
