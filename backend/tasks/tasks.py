import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .formatters import format_task
from .models import Reminder, Task
from notifications.publisher import publish_telegram_message
from users.models import User
from .services.habits import build_habits_report

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def send_task_reminders(self: Task) -> None:
    now = timezone.now()

    reminders = Reminder.objects.select_related("task", "task__user").filter(
        sent=False,
        notify_at__lte=now,
        task__status=Task.Status.PENDING,
    )

    for reminder in reminders:
        task = reminder.task
        user = task.user

        if not user.telegram_id:
            logger.warning(
                "User has no telegram_id",
                extra={"user_id": user.id, "task_id": task.id},
            )
            continue

        publish_telegram_message(
            telegram_id=user.telegram_id,
            text=_build_task_reminder_text(task),
            extra={"task_id": str(task.id), "reminder_id": str(reminder.id)},
        )

        reminder.sent = True
        reminder.save(update_fields=["sent"])

        logger.info(
            "Reminder sent",
            extra={"task_id": task.id, "user_id": user.id},
        )


def _build_task_reminder_text(task: Task) -> str:
    return f"⏰ <b>Напоминание о задаче</b>\n\n{format_task(task)}"


@shared_task(  # type: ignore
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def send_weekly_habits_reports(self: Task) -> None:
    now = timezone.now()
    cutoff = now - timedelta(days=7)

    users = (
        User.objects.filter(is_active=True)
        .filter(telegram_id__isnull=False)
        .filter(
            Q(last_habits_report_at__lt=cutoff) | Q(last_habits_report_at__isnull=True)
        )
    )

    use_llm = getattr(settings, "HUGGINGFACE_USE_LLM_WEEKLY", True)

    for user in users.iterator():
        report = build_habits_report(user, days=7, use_llm=use_llm)
        publish_telegram_message(
            telegram_id=user.telegram_id,
            text=report.short_text,
            extra={"user_id": str(user.id), "type": "habits_short"},
        )
        publish_telegram_message(
            telegram_id=user.telegram_id,
            text=report.long_text,
            extra={"user_id": str(user.id), "type": "habits_long"},
        )
        user.last_habits_report_at = now
        user.save(update_fields=["last_habits_report_at"])
