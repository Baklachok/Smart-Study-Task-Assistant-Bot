import logging
from typing import Any

import httpx

from bot.celery_app import celery_app
from bot.config import settings

logger = logging.getLogger(__name__)

BOT_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@celery_app.task(  # type: ignore
    name="bot.send_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def send_message(
    self: Any,
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    extra: dict[str, object] | None = None,
) -> None:
    response = httpx.post(
        f"{BOT_API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        },
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(
            "Failed to send telegram message",
            extra={
                "telegram_id": chat_id,
                "status": response.status_code,
                "response": response.text,
                "payload_extra": extra,
            },
        )
        raise RuntimeError("Telegram sendMessage failed")
