from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.http import task_api_request
from bot.utils.telegram_helpers import require_auth

CANCEL_TEXT = "❌ Отмена"
CANCEL_CALLBACK = "cancel"

# --- Универсальная клавиатура с кнопкой "Отмена" ---
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def add_cancel_inline(kb: InlineKeyboardMarkup | None = None) -> InlineKeyboardMarkup:
    """
    Добавляет кнопку отмены к существующей InlineKeyboardMarkup
    или создаёт новую клавиатуру с одной кнопкой отмены.
    """
    builder = InlineKeyboardBuilder()

    # если есть существующие кнопки, добавляем их
    if kb and kb.inline_keyboard:
        for row in kb.inline_keyboard:
            for btn in row:
                builder.button(text=btn.text, callback_data=btn.callback_data)

    # добавляем кнопку отмены
    builder.button(text=CANCEL_TEXT, callback_data=CANCEL_CALLBACK)

    return builder.as_markup()


# --- Хендлер отмены для текстовых сообщений ---
async def handle_cancel_message(message: Message, state: FSMContext) -> bool:
    """
    Проверяет, нажал ли пользователь "Отмена" в текстовом сообщении.
    Если да, очищает состояние и возвращает True.
    """
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Действие отменено")
        return True
    return False


# --- Хендлер отмены для callback ---
async def handle_cancel_callback(callback: CallbackQuery, state: FSMContext) -> bool:
    """
    Проверяет, нажал ли пользователь кнопку "Отмена" в callback.
    Если да, очищает состояние и возвращает True.
    """
    if callback.data == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Действие отменено")
        await callback.answer()
        return True
    return False


async def perform_task_action(
    callback: CallbackQuery,
    task_id: str | None,
    action: str,
    success_text: str,
) -> None:
    """Универсальный обработчик действий с задачами (done/delete)."""
    token = await require_auth(callback)
    if not token:
        return

    method, payload = {
        "done": ("patch", {"status": "done"}),
        "delete": ("delete", None),
    }.get(action, (None, None))

    if not method:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    resp = await task_api_request(task_id, method, token, payload)
    if (action == "done" and resp.status_code == 200) or (
        action == "delete" and resp.status_code == 204
    ):
        await callback.message.edit_text(success_text)
        await callback.answer()
    else:
        await callback.answer("Ошибка ❌", show_alert=True)
