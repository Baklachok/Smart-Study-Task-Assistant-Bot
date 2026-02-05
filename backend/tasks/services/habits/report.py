from __future__ import annotations

from datetime import timedelta
from typing import Any
import logging

from django.utils import timezone

from tasks.models import Task
from users.models import User
from users.utils.timezone import get_user_timezone

from .types import DAY_NAMES, HabitsReport
from .llm import (
    build_llm_prompt,
    call_hf_api,
    clean_llm_text,
    fallback_split,
    parse_llm_response,
)

logger = logging.getLogger(__name__)


def _percent(value: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(round((value / total) * 100))


def _build_suggestions(
    done_count: int,
    overdue_percent: int,
    reminder_help_rate: int,
    no_due_rate: int,
    best_day: str,
    best_hour: int | None,
    best_hour_text: str,
) -> list[str]:
    suggestions: list[str] = []
    if done_count == 0:
        suggestions.append("Начни с 1–2 коротких задач в день, чтобы закрепить ритм.")
    else:
        if overdue_percent >= 40:
            suggestions.append(
                "Попробуй ставить дедлайны раньше и включать напоминания."
            )
        if reminder_help_rate < 30 and done_count >= 5:
            suggestions.append(
                "Напоминания редко помогают — попробуй добавить напоминание за 2–4 часа."
            )
        if no_due_rate >= 50:
            suggestions.append(
                "Большинство задач без дедлайна — дедлайн повышает шанс завершения."
            )
        if best_day != "—" and best_hour is not None:
            suggestions.append(
                f"Лучшее время — {best_day} {best_hour_text}. Планируй важное на этот слот."
            )

    if not suggestions:
        suggestions.append(
            "Продолжай в том же темпе и закрепляй удачные временные окна."
        )

    return suggestions


def _build_rule_texts(
    days: int, stats: dict[str, Any], suggestions: list[str]
) -> tuple[str, str]:
    short_lines = [
        f"🧠 Привычки за последние {days} дн.",
        f"✅ Выполнено: {stats['done_count']} из {stats['created_count']}",
        (
            f"⏱ В срок: {stats['on_time_percent']}% ({stats['on_time_count']} из {stats['due_done_count']})"
            if stats["due_done_count"]
            else "⏱ В срок: — (нет дедлайнов)"
        ),
        f"🌟 Лучшее время: {stats['best_day']}, {stats['best_hour_text']}",
    ]

    long_lines = [
        f"Создано задач: {stats['created_count']}",
        f"Завершено: {stats['done_count']}",
        (
            f"В срок: {stats['on_time_count']} из {stats['due_done_count']} ({stats['on_time_percent']}%)"
            if stats["due_done_count"]
            else "В срок: — (нет задач с дедлайнами)"
        ),
        (
            f"Просрочено: {stats['overdue_count']} из {stats['due_done_count']} ({stats['overdue_percent']}%)"
            if stats["due_done_count"]
            else "Просрочено: —"
        ),
        f"Без дедлайна: {stats['no_due_count']} ({stats['no_due_rate']}%)",
        f"Напоминания помогли: {stats['reminder_helped_tasks']} задач ({stats['reminder_help_rate']}%)",
        f"Пик завершения: {stats['best_day']}, {stats['best_hour_text']}",
        "Рекомендации:",
        *[f"• {tip}" for tip in suggestions],
    ]

    return "\n".join(short_lines), "\n".join(long_lines)


def _apply_llm_overlay(
    short_text: str,
    long_text: str,
    metrics: dict[str, object],
    user: User,
    days: int,
) -> tuple[str, str]:
    language = getattr(user, "language", "ru")
    prompt = build_llm_prompt(metrics, days, language)
    llm_text = call_hf_api(prompt)
    if not llm_text:
        logger.info(
            "LLM fallback to rule-based report",
            extra={"user_id": str(user.id), "days": days},
        )
        return short_text, long_text

    llm_short, llm_long, llm_tips = parse_llm_response(llm_text)
    fallback_short, fallback_long = fallback_split(llm_text)
    looks_like_dict = "short" in llm_text and "long" in llm_text and "{" in llm_text

    if llm_short or llm_long:
        short_text = (
            clean_llm_text(llm_short) if llm_short else clean_llm_text(fallback_short)
        )
        if llm_long:
            long_text = clean_llm_text(llm_long)
        elif looks_like_dict:
            long_text = short_text
        else:
            long_text = clean_llm_text(fallback_long)
    else:
        short_text = clean_llm_text(fallback_short) if fallback_short else ""
        long_text = clean_llm_text(fallback_long) if fallback_long else ""

    if long_text.lstrip().startswith("{"):
        long_text = short_text

    if llm_tips:
        tips_block = "\n".join(f"• {tip}" for tip in llm_tips)
        if long_text:
            long_text = f"{long_text}\nРекомендации:\n{tips_block}"
        else:
            long_text = f"Рекомендации:\n{tips_block}"

    logger.info(
        "LLM report generated",
        extra={"user_id": str(user.id), "days": days},
    )
    return short_text, long_text


def build_habits_report(
    user: User, days: int = 30, use_llm: bool = True
) -> HabitsReport:
    now = timezone.now()
    start = now - timedelta(days=days)
    user_tz = get_user_timezone(user)

    created_count = Task.objects.filter(
        user=user, created_at__gte=start, created_at__lte=now
    ).count()

    done_tasks = (
        Task.objects.filter(
            user=user,
            status=Task.Status.DONE,
            completed_at__isnull=False,
            completed_at__gte=start,
            completed_at__lte=now,
        )
        .prefetch_related("reminders")
        .all()
    )

    done_count = 0
    due_done_count = 0
    on_time_count = 0
    overdue_count = 0
    no_due_count = 0
    reminder_helped_tasks = 0
    reminders_sent_before_done = 0

    by_day = [0] * 7
    by_hour = [0] * 24

    for task in done_tasks:
        if not task.completed_at:
            continue
        done_count += 1
        completed_local = timezone.localtime(task.completed_at, user_tz)
        by_day[completed_local.weekday()] += 1
        by_hour[completed_local.hour] += 1

        if task.due_at:
            due_done_count += 1
            if task.completed_at <= task.due_at:
                on_time_count += 1
            else:
                overdue_count += 1
        else:
            no_due_count += 1

        reminders = list(task.reminders.all())
        reminder_before_done = False
        for reminder in reminders:
            if reminder.sent and reminder.notify_at <= task.completed_at:
                reminders_sent_before_done += 1
                reminder_before_done = True
        if reminder_before_done:
            reminder_helped_tasks += 1

    best_day_idx = max(range(7), key=by_day.__getitem__) if done_count else None
    best_hour = max(range(24), key=by_hour.__getitem__) if done_count else None

    best_day = DAY_NAMES[best_day_idx] if best_day_idx is not None else "—"
    best_hour_text = f"{best_hour:02d}:00" if best_hour is not None else "—"

    on_time_percent = _percent(on_time_count, due_done_count)
    overdue_percent = _percent(overdue_count, due_done_count)
    reminder_help_rate = _percent(reminder_helped_tasks, done_count)
    no_due_rate = _percent(no_due_count, done_count)

    suggestions = _build_suggestions(
        done_count=done_count,
        overdue_percent=overdue_percent,
        reminder_help_rate=reminder_help_rate,
        no_due_rate=no_due_rate,
        best_day=best_day,
        best_hour=best_hour,
        best_hour_text=best_hour_text,
    )

    stats = {
        "created_count": created_count,
        "done_count": done_count,
        "due_done_count": due_done_count,
        "on_time_count": on_time_count,
        "on_time_percent": on_time_percent,
        "overdue_count": overdue_count,
        "overdue_percent": overdue_percent,
        "no_due_count": no_due_count,
        "no_due_rate": no_due_rate,
        "reminder_helped_tasks": reminder_helped_tasks,
        "reminder_help_rate": reminder_help_rate,
        "best_day": best_day,
        "best_hour_text": best_hour_text,
    }

    short_text, long_text = _build_rule_texts(days, stats, suggestions)

    metrics = {
        "period_days": days,
        "period_start": start.isoformat(),
        "period_end": now.isoformat(),
        "counts": {
            "created": created_count,
            "completed": done_count,
            "completed_on_time": on_time_count,
            "completed_overdue": overdue_count,
            "completed_no_due": no_due_count,
            "completed_with_reminder": reminder_helped_tasks,
            "reminders_sent_before_done": reminders_sent_before_done,
        },
        "patterns": {
            "best_day": best_day,
            "best_hour": best_hour,
        },
        "rates": {
            "on_time_percent": on_time_percent,
            "overdue_percent": overdue_percent,
            "reminder_help_rate": reminder_help_rate,
            "no_due_rate": no_due_rate,
        },
        "suggestions": suggestions,
    }

    if use_llm:
        short_text, long_text = _apply_llm_overlay(
            short_text, long_text, metrics, user, days
        )

    return HabitsReport(short_text=short_text, long_text=long_text, metrics=metrics)
