import logging

from celery import shared_task
from django.utils import timezone

from .formatters import format_task
from .models import Reminder, Task
from ..notifications.publisher import publish_telegram_message

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
        sent=False, notify_at__lte=now
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
