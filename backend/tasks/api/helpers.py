import logging
from datetime import timedelta
from typing import Any, cast

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User

from ..models import Task
from ..services.reminders import create_default_reminders

logger = logging.getLogger(__name__)

FILTER_TODAY = "today"
FILTER_WEEK = "week"
DEFAULT_HABITS_DAYS = 30
MIN_HABITS_DAYS = 7
MAX_HABITS_DAYS = 90

TaskSnapshot = dict[str, Any]
ChangedFields = dict[str, dict[str, Any]]


def log_task_action(
    action: str,
    task: Task,
    user_id: int | str,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    extra = {
        "task_id": task.id,
        "user_id": user_id,
        "topic_id": getattr(task, "topic_id", None),
    }
    if extra_fields:
        extra.update(extra_fields)
    logger.info(f"Task {action}", extra=extra)


class TaskUserMixin:
    def get_request(self) -> Request:
        return cast(Request, getattr(self, "request"))

    def get_user(self) -> User:
        return cast(User, self.get_request().user)


def build_task_list_queryset(request: Request, user: User) -> QuerySet[Any]:
    queryset = Task.objects.filter(user=user)
    filter_by = request.query_params.get("filter")
    topic_id = request.query_params.get("topic")
    now = timezone.now()

    logger.debug(
        "Tasks list requested",
        extra={"user_id": user.id, "filter": filter_by, "topic_id": topic_id},
    )

    queryset = _apply_date_filter(queryset, filter_by, now)
    return _apply_topic_filter(queryset, topic_id)


def handle_created_task(task: Task, user_id: int | str) -> None:
    create_default_reminders(task)
    log_task_action(
        "created",
        task,
        user_id,
        extra_fields={
            "title": task.title,
            "due_at": task.due_at,
            "priority": task.priority,
        },
    )


def log_retrieved_task(task: Task, user_id: int | str) -> None:
    logger.debug("Task retrieved", extra={"task_id": task.id, "user_id": user_id})


def snapshot_task_fields(task: Task, validated_data: dict[str, Any]) -> TaskSnapshot:
    return {field: getattr(task, field) for field in validated_data}


def handle_updated_task(task: Task, old_data: TaskSnapshot) -> None:
    changed_fields = _build_changed_fields(task, old_data)
    _handle_due_at_change(task, changed_fields)
    _handle_status_change(task, changed_fields)
    user = cast(User, task.user)
    log_task_action(
        "updated",
        task,
        user.id,
        extra_fields={"changed_fields": changed_fields},
    )


def handle_deleted_task(task: Task) -> None:
    user = cast(User, task.user)
    log_task_action(
        "deleted",
        task,
        user.id,
        extra_fields={"title": task.title},
    )
    task.delete()


def parse_habits_days(request: Request) -> int | Response:
    days_raw = request.query_params.get("days", str(DEFAULT_HABITS_DAYS))
    try:
        days = int(days_raw)
    except ValueError:
        return Response({"detail": "Invalid days value"}, status=400)

    if days < MIN_HABITS_DAYS or days > MAX_HABITS_DAYS:
        return Response(
            {
                "detail": f"Days must be between {MIN_HABITS_DAYS} and {MAX_HABITS_DAYS}"
            },
            status=400,
        )

    return days


def serialize_habits_report(report: Any) -> dict[str, Any]:
    return {
        "short_text": report.short_text,
        "long_text": report.long_text,
        "metrics": report.metrics,
    }


def _apply_date_filter(
    queryset: QuerySet[Any], filter_by: str | None, now: Any
) -> QuerySet[Any]:
    if filter_by == FILTER_TODAY:
        queryset = queryset.filter(due_at__date=now.date())
    elif filter_by == FILTER_WEEK:
        end_week = now + timedelta(days=7)
        queryset = queryset.filter(due_at__date__range=(now.date(), end_week.date()))
    return queryset


def _apply_topic_filter(queryset: QuerySet[Any], topic_id: str | None) -> QuerySet[Any]:
    if topic_id:
        queryset = queryset.filter(topic_id=topic_id)
    return queryset


def _build_changed_fields(task: Task, old_data: TaskSnapshot) -> ChangedFields:
    return {
        field: {"old": old_data[field], "new": getattr(task, field)}
        for field in old_data
        if old_data[field] != getattr(task, field)
    }


def _handle_due_at_change(task: Task, changed_fields: ChangedFields) -> None:
    if "due_at" not in changed_fields:
        return
    reminders_manager = cast(Any, getattr(task, "reminders"))
    reminders_manager.all().delete()
    create_default_reminders(task)


def _handle_status_change(task: Task, changed_fields: ChangedFields) -> None:
    if "status" not in changed_fields:
        return
    _sync_completed_at(task)


def _sync_completed_at(task: Task) -> None:
    completed_at = timezone.now() if task.status == Task.Status.DONE else None
    Task.objects.filter(pk=task.pk).update(completed_at=completed_at)
