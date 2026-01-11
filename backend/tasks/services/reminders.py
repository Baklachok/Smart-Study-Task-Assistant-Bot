import logging
from datetime import timedelta

from django.utils import timezone
from datetime import timezone as dt_timezone

from tasks.models import Reminder, Task

from users.utils.timezone import get_user_timezone

logger = logging.getLogger(__name__)

DEFAULT_REMINDER_OFFSETS = (
    timedelta(days=1),
    timedelta(hours=1),
)


def create_default_reminders(task: Task) -> None:
    """
    Создает напоминания относительно due_at.
    """
    if not task.due_at:
        logger.debug(
            "Task has no due_at, skipping reminder creation",
            extra={
                "task_id": task.id,
                "user_id": task.user_id,
            },
        )
        return

    user_tz = get_user_timezone(task.user)
    due_local = task.due_at.astimezone(user_tz)
    now_local = timezone.now().astimezone(user_tz)

    reminders: list[Reminder] = []

    logger.debug(
        "Creating default reminders for task",
        extra={
            "task_id": task.id,
            "user_id": task.user_id,
            "due_at": due_local,
            "offsets": [str(o) for o in DEFAULT_REMINDER_OFFSETS],
        },
    )

    for offset in DEFAULT_REMINDER_OFFSETS:
        notify_at_local = due_local - offset

        if notify_at_local <= now_local:
            logger.debug(
                "Skipping reminder in the past",
                extra={
                    "task_id": task.id,
                    "notify_at": notify_at_local,
                    "offset": str(offset),
                },
            )
            continue

        notify_at_utc = notify_at_local.astimezone(dt_timezone.utc)
        reminders.append(Reminder(task=task, notify_at=notify_at_utc))

    if not reminders:
        logger.info(
            "No reminders created (all notify_at in the past)",
            extra={
                "task_id": task.id,
                "user_id": task.user_id,
            },
        )
        return

    Reminder.objects.bulk_create(reminders)

    logger.info(
        "Default reminders created",
        extra={
            "task_id": task.id,
            "user_id": task.user_id,
            "count": len(reminders),
            "notify_at_list": [r.notify_at for r in reminders],
        },
    )
