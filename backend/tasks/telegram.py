import logging
import os

import httpx

from .models import Task
from bot.formatters.tasks import format_task


logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(telegram_id: int, text: str) -> None:
    response = httpx.post(
        f"{BOT_API_URL}/sendMessage",
        json={
            "chat_id": telegram_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(
            "Failed to send telegram message",
            extra={
                "telegram_id": telegram_id,
                "status": response.status_code,
                "response": response.text,
            },
        )


def _build_task_reminder_text(task: Task) -> str:
    return f"⏰ <b>Напоминание о задаче</b>\n\n{format_task(task)}"
