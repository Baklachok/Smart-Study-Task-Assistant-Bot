import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.habits import fetch_habits_report
from bot.utils.telegram_helpers import require_auth, send_message_with_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("habits"))  # type: ignore
async def habits_handler(message: Message) -> None:
    token = await require_auth(message)
    if not token:
        return

    response = await fetch_habits_report(token, days=30)
    if response.status_code != 200:
        logger.error("Habits report failed: %s %s", response.status_code, response.text)
        await send_message_with_kb(message, "Ошибка загрузки отчета ❌")
        return

    data = response.json()
    long_text = data.get("long_text") or "Нет данных для отчета."
    await send_message_with_kb(message, long_text)
