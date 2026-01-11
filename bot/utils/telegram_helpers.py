import logging
from typing import Optional, Any
from aiogram.types import Message, CallbackQuery, InaccessibleMessage

from bot.keyboards.courses import make_inline_kb
from bot.utils.auth import get_access_token

logger = logging.getLogger(__name__)


async def safe_edit_text(
    message: Message | InaccessibleMessage | None, text: str
) -> None:
    """Безопасно редактируем сообщение, если оно доступно"""
    if message and hasattr(message, "edit_text"):
        try:
            await message.edit_text(text)
            logger.info("Сообщение успешно обновлено: %s", text)
        except Exception as e:
            logger.error("Ошибка при редактировании сообщения: %s", e)
    else:
        logger.warning("Сообщение недоступно для редактирования")


def extract_task_id(data: str | None, prefix: str) -> Optional[str]:
    """Извлекает task_id из callback_data"""
    if not data:
        logger.warning("Пустые данные callback")
        return None
    if not data.startswith(prefix):
        logger.warning("Данные не соответствуют префиксу %s: %s", prefix, data)
        return None

    task_id = data.split(":", 1)[1]
    logger.info("Извлечен task_id: %s", task_id)
    return task_id


async def require_auth(obj: Message | CallbackQuery) -> str | None:
    logger.warning("Unauthorized action from user")
    token = get_access_token(obj)
    if not token:
        if isinstance(obj, Message):
            await obj.answer("Сначала авторизуйтесь через /start")
        else:
            await obj.answer("Сначала /start", show_alert=True)
        return None
    return token


async def send_message_with_kb(
    message_obj: Any, text: str, buttons: list[dict[str, str]] | None = None
) -> None:
    """Отправка сообщения с опциональными кнопками"""
    kb = make_inline_kb(buttons) if buttons else None
    await message_obj.answer(text, reply_markup=kb, parse_mode="HTML")
