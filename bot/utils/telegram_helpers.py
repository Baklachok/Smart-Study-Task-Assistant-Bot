import logging
from typing import Optional, Iterable, Union

from aiogram.types import (
    Message,
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.utils.auth import get_access_token

logger = logging.getLogger(__name__)


CANCEL_CALLBACK = "cancel"

CANCEL_BUTTON: dict[str, str] = {
    "text": "❌ Отмена",
    "callback_data": CANCEL_CALLBACK,
}

EditableMessage = Union[Message, InaccessibleMessage]
TelegramMessage = Union[Message, CallbackQuery]


async def safe_edit_text(
    message: Optional[EditableMessage],
    text: str,
) -> None:
    """
    Безопасно редактирует сообщение, если это возможно.
    """
    if message is None:
        logger.warning("safe_edit_text: message is None")
        return

    if not hasattr(message, "edit_text"):
        logger.warning(
            "safe_edit_text: edit_text not supported (%s)",
            type(message).__name__,
        )
        return

    try:
        await message.edit_text(text)
        logger.debug("Message edited successfully")
    except Exception:
        logger.exception("Failed to edit message")


def extract_id_from_callback(
    data: Optional[str],
    prefix: str,
) -> Optional[str]:
    """
    Извлекает id из callback_data формата '<prefix>:<id>'.
    """
    if not data:
        logger.warning("extract_id_from_callback: empty callback data")
        return None

    if not data.startswith(prefix):
        logger.warning(
            "extract_id_from_callback: invalid prefix (expected=%s, got=%s)",
            prefix,
            data,
        )
        return None

    _, entity_id = data.split(":", 1)
    logger.debug("extract_id_from_callback: id=%s", entity_id)
    return entity_id


async def require_auth(target: TelegramMessage) -> Optional[str]:
    """
    Проверяет авторизацию пользователя и возвращает access token.
    """
    token = get_access_token(target)

    if token:
        logger.debug("require_auth: auth success")
        return token

    logger.warning("require_auth: unauthorized user")

    if isinstance(target, Message):
        await target.answer("Сначала авторизуйтесь через /start")
    else:
        await target.answer("Сначала /start", show_alert=True)

    return None


def with_cancel(
    buttons: Optional[Iterable[dict[str, str]]],
) -> list[dict[str, str]]:
    """
    Добавляет кнопку отмены к списку кнопок.
    """
    result = list(buttons or [])
    result.append(CANCEL_BUTTON)

    logger.debug("with_cancel: buttons_count=%d", len(result))
    return result


def build_inline_kb(
    buttons: list[dict[str, str]],
) -> InlineKeyboardMarkup:
    """
    Строит InlineKeyboardMarkup из списка словарей.
    """
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
    target: TelegramMessage,
    text: str,
    buttons: Optional[Union[list[dict[str, str]], InlineKeyboardMarkup]] = None,
) -> None:
    """
    Отправляет сообщение с inline-клавиатурой (если есть).
    """
    reply_markup = build_inline_kb(buttons) if isinstance(buttons, list) else buttons

    logger.debug(
        "send_message_with_kb: target=%s, text=%r",
        type(target).__name__,
        text,
    )

    if isinstance(target, Message):
        await target.answer(text, reply_markup=reply_markup)
        return

    await target.message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    await target.answer()


def normalize_buttons(
    buttons: Iterable[tuple[str, str] | dict[str, str]],
) -> list[dict[str, str]]:
    """
    Нормализует кнопки в формат:
    { "text": str, "callback_data": str }
    """
    result: list[dict[str, str]] = []

    for btn in buttons:
        if isinstance(btn, tuple):
            text, callback_data = btn
            result.append({"text": text, "callback_data": callback_data})
        else:
            result.append(btn)

    return result
