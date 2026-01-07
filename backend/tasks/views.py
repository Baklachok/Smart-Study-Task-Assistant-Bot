import logging
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from .models import Task
from .permissions import IsOwner
from .serializers import TaskSerializer


logger = logging.getLogger(__name__)


def log_task_action(
    action: str, task: Task, user_id: int, extra_fields: dict | None = None
):
    """Универсальный логгер для действий с задачами"""
    extra = {
        "task_id": task.id,
        "user_id": user_id,
        "topic_id": getattr(task, "topic_id", None),
    }
    if extra_fields:
        extra.update(extra_fields)
    logger.info(f"Task {action}", extra=extra)


@extend_schema(request=TaskSerializer, tags=["Tasks"])
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        filter_by = self.request.query_params.get("filter")
        now = timezone.now()

        logger.debug(
            "Tasks list requested", extra={"user_id": user.id, "filter": filter_by}
        )

        queryset = Task.objects.filter(user=user)

        if filter_by == "today":
            queryset = queryset.filter(due_at__date=now.date())
        elif filter_by == "week":
            end_week = now + timedelta(days=7)
            queryset = queryset.filter(
                due_at__date__range=(now.date(), end_week.date())
            )

        return queryset

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        log_task_action(
            "created",
            task,
            self.request.user.id,
            extra_fields={
                "title": task.title,
                "due_at": task.due_at,
                "priority": task.priority,
            },
        )


@extend_schema(request=TaskSerializer, tags=["Tasks"])
class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Task.objects.all()

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        logger.debug(
            "Task retrieved", extra={"task_id": task.id, "user_id": request.user.id}
        )
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
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

        log_task_action(
            "updated",
            updated_task,
            updated_task.user_id,
            extra_fields={"changed_fields": changed_fields},
        )

    def perform_destroy(self, instance):
        log_task_action(
            "deleted",
            instance,
            instance.user_id,
            extra_fields={"title": instance.title},
        )
        instance.delete()
