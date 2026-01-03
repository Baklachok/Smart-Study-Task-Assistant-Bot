from datetime import datetime
from typing import Optional


PRIORITY_EMOJI = {
    "low": "🟢 low",
    "medium": "🟡 medium",
    "high": "🔴 high",
}


def format_priority(priority: Optional[str]) -> str:
    if priority is None:
        return "—"
    return PRIORITY_EMOJI.get(priority, "—")


def format_due_at(due_at: Optional[str]) -> str:
    if not due_at:
        return "—"
    try:
        dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return due_at
