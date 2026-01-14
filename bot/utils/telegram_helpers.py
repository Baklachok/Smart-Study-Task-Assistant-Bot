import logging
from typing import Optional, Iterable

from aiogram.types import (
    Message,
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.utils.auth import get_access_token

logger = logging.getLogger(__name__)


CANCEL_BUTTON: dict[str, str] = {
    "text": "❌ Отмена",
    "callback_data": "cancel",
}


async def safe_edit_text(
    message: Message | InaccessibleMessage | None,
    text: str,
) -> None:
    if not message:
        logger.warning("safe_edit_text: message is None")
        return

    if not hasattr(message, "edit_text"):
        logger.warning(
            "safe_edit_text: message has no edit_text method (%s)",
            type(message),
        )
        return

    try:
        await message.edit_text(text)
        logger.info("Message edited successfully: %s", text)
    except Exception:
        logger.exception("Failed to edit message")


def extract_task_id(data: str | None, prefix: str) -> Optional[str]:
    """Извлекает task_id из callback_data"""
    if not data:
        logger.warning("extract_task_id: empty callback data")
        return None

    if not data.startswith(prefix):
        logger.warning(
            "extract_task_id: invalid prefix (expected=%s, got=%s)",
            prefix,
            data,
        )
        return None

    task_id = data.split(":", 1)[1]
    logger.debug("extract_task_id: extracted task_id=%s", task_id)
    return task_id


async def require_auth(obj: Message | CallbackQuery) -> Optional[str]:
    token = get_access_token(obj)

    if not token:
        logger.warning("require_auth: unauthorized user")

        if isinstance(obj, Message):
            await obj.answer("Сначала авторизуйтесь через /start")
        else:
            await obj.answer("Сначала /start", show_alert=True)

        return None

    logger.debug("require_auth: auth success")
    return token


def with_cancel(
    buttons: Iterable[dict[str, str]] | None,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = list(buttons or [])
    result.append(CANCEL_BUTTON)

    logger.debug("with_cancel: buttons_count=%d", len(result))
    return result


def build_inline_kb(buttons: list[dict[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn["callback_data"],
                )
            ]
            for btn in buttons
        ]
    )


async def send_message_with_kb(
    target: Message | CallbackQuery,
    text: str,
    buttons: list[dict[str, str]] | None = None,
) -> None:
    reply_markup = build_inline_kb(buttons) if buttons else None

    if isinstance(target, Message):
        logger.debug(
            "send_message_with_kb: target=Message, text=%r, buttons=%s",
            text,
            buttons,
        )
        await target.answer(text, reply_markup=reply_markup)

    elif isinstance(target, CallbackQuery):
        logger.debug(
            "send_message_with_kb: target=CallbackQuery, text=%r, buttons=%s",
            text,
            buttons,
        )
        await target.message.answer(text, reply_markup=reply_markup)
        await target.answer()
