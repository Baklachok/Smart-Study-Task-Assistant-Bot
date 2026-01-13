from datetime import datetime
from typing import Any

PRIORITY_EMOJI: dict[str, str] = {
    "low": "🟢 low",
    "medium": "🟡 medium",
    "high": "🔴 high",
}


def format_priority(priority: str | None) -> str:
    """Форматирование приоритета задачи в emoji + текст"""
    return PRIORITY_EMOJI.get(priority or "", "—")


def format_due_at(due_at: str | None) -> str:
    """Форматирование даты дедлайна в вид 'DD.MM.YYYY HH:MM'"""
    if not due_at:
        return "—"
    try:
        dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return due_at


def _get(obj: Any, key: str) -> Any:
    """Достаёт поле и из dict, и из объекта"""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def format_task(task: Any) -> str:
    title = _get(task, "title") or "—"
    description = _get(task, "description") or "—"
    priority = _get(task, "priority")
    status = _get(task, "status") or "—"

    topic_obj = _get(task, "topic") or "—"
    if isinstance(topic_obj, dict):
        topic = topic_obj.get("title", "—")
    else:
        topic = topic_obj

    due_at = _get(task, "due_at")
    if hasattr(due_at, "isoformat"):
        due_at = due_at.isoformat()

    return (
        f"📝 <b>{title}</b>\n"
        f"📄 {description}\n"
        f"⏰ Дедлайн: {format_due_at(due_at)}\n"
        f"⚡ Приоритет: {format_priority(priority)}\n"
        f"📘 Тема: {topic}\n"
        f"📌 Статус: {status}"
    )
