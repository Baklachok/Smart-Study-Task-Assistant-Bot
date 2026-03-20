from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .models import Task
from .permissions import IsOwner
from .serializers import HabitsReportSerializer, TaskSerializer
from .services.habits import build_habits_report
from .api.helpers import (
    TaskUserMixin,
    build_task_list_queryset,
    handle_created_task,
    handle_deleted_task,
    handle_updated_task,
    log_retrieved_task,
    parse_habits_days,
    serialize_habits_report,
    snapshot_task_fields,
)
from .api.schema import HABITS_REPORT_PARAMETERS, TASK_LIST_PARAMETERS
from users.models import User


@extend_schema_view(
    get=extend_schema(
        tags=["Tasks"],
        summary="Список задач",
        parameters=TASK_LIST_PARAMETERS,
    ),
    post=extend_schema(
        tags=["Tasks"],
        summary="Создать задачу",
    ),
)
class TaskListCreateView(TaskUserMixin, generics.ListCreateAPIView):
    """Список задач и создание новой задачи."""

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.none()

    def get_queryset(self) -> QuerySet[Any]:
        return build_task_list_queryset(self.get_request(), self.get_user())

    def perform_create(self, serializer: BaseSerializer) -> None:
        user = self.get_user()
        task = serializer.save(user=user)
        handle_created_task(task, user.id)


@extend_schema(tags=["Tasks"])
class TaskDetailView(TaskUserMixin, generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, обновление и удаление задачи."""

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Task.objects.all()

    def retrieve(
        self, request: Request, *args: Any, **kwargs: dict[str, Any]
    ) -> Response:
        task = self.get_object()
        log_retrieved_task(task, self.get_user().id)
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer: BaseSerializer) -> None:
        task = self.get_object()
        old_data = snapshot_task_fields(task, serializer.validated_data)
        updated_task = serializer.save()
        handle_updated_task(updated_task, old_data)

    def perform_destroy(self, instance: Task) -> None:
        handle_deleted_task(instance)


@extend_schema(
    tags=["Habits"],
    summary="Отчет по привычкам",
    description="Возвращает краткую и подробную аналитику привычек пользователя.",
    parameters=HABITS_REPORT_PARAMETERS,
    responses={200: HabitsReportSerializer},
)
class HabitsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HabitsReportSerializer

    def get(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> Response:
        days = parse_habits_days(request)
        if isinstance(days, Response):
            return days

        report = build_habits_report(cast(User, request.user), days=days, use_llm=True)
        return Response(serialize_habits_report(report))
