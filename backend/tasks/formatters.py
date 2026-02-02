from datetime import datetime

from django.utils import timezone

from typing import cast

from ..topics.models import Topic
from .models import Task

PRIORITY_EMOJI: dict[str, str] = {
    "low": "🟢 low",
    "medium": "🟡 medium",
    "high": "🔴 high",
}


def _format_priority(priority: str | None) -> str:
    return PRIORITY_EMOJI.get(priority or "", "—")


def _format_due_at(due_at: datetime | None) -> str:
    if not due_at:
        return "—"
    return timezone.localtime(due_at).strftime("%d.%m.%Y %H:%M")


def format_task(task: Task) -> str:
    title = task.title or "—"
    description = task.description or "—"
    topic_obj = cast(Topic | None, task.topic)
    topic = topic_obj.title if topic_obj else "—"

    return (
        f"📝 <b>{title}</b>\n"
        f"📄 {description}\n"
        f"⏰ Дедлайн: {_format_due_at(task.due_at)}\n"
        f"⚡ Приоритет: {_format_priority(task.priority)}\n"
        f"📘 Тема: {topic}\n"
        f"📌 Статус: {task.status}"
    )
