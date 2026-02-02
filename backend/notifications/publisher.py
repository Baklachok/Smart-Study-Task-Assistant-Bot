import logging
from typing import Any

from celery import current_app
from django.conf import settings

logger = logging.getLogger(__name__)


def publish_telegram_message(
    *,
    telegram_id: int,
    text: str,
    parse_mode: str = "HTML",
    extra: dict[str, Any] | None = None,
) -> None:
    task_name = getattr(settings, "BOT_SEND_MESSAGE_TASK", "bot.send_message")
    queue_name = getattr(settings, "BOT_QUEUE", "telegram")

    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": parse_mode,
        "extra": extra or {},
    }

    logger.info(
        "Publishing telegram message",
        extra={
            "telegram_id": telegram_id,
            "task_name": task_name,
            "queue": queue_name,
        },
    )

    current_app.send_task(task_name, kwargs=payload, queue=queue_name)
