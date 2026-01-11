from datetime import datetime
from typing import Any, Mapping

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


def format_task(task: Mapping[str, Any]) -> str:
    """
    Форматирование задачи в строку для Telegram
    task: словарь с ключами 'title', 'description', 'due_at', 'priority', 'status'
    """
    title = task.get("title", "—")
    description = task.get("description") or "—"
    due_at = format_due_at(task.get("due_at"))
    priority = format_priority(task.get("priority"))
    status = task.get("status", "—")

    return (
        f"📝 <b>{title}</b>\n"
        f"📄 {description}\n"
        f"⏰ Дедлайн: {due_at}\n"
        f"⚡ Приоритет: {priority}\n"
        f"📌 Статус: {status}"
    )
