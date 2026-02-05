import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logger = logging.getLogger(__name__)
router = Router()

MENU_MESSAGE_ID: dict[int, int] = {}

MENU_TITLE = "Главное меню\nВыберите раздел 👇"
MENU_PREFIX = "menu:"

SECTION_TEXT: dict[str, str] = {
    "tasks": "Раздел «Задачи»\n(Скоро здесь появится управление задачами.)",
    "habits": "Раздел «Привычки»\n(Скоро здесь появится аналитика.)",
    "courses": "Раздел «Курсы»\n(Скоро здесь появится управление курсами.)",
    "topics": "Раздел «Темы»\n(Скоро здесь появится управление темами.)",
    "help": "Помощь\n(Скоро здесь появятся подсказки.)",
}


def _main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Задачи", callback_data=f"{MENU_PREFIX}tasks"
                ),
                InlineKeyboardButton(
                    text="🧠 Привычки", callback_data=f"{MENU_PREFIX}habits"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📚 Курсы", callback_data=f"{MENU_PREFIX}courses"
                ),
                InlineKeyboardButton(
                    text="📘 Темы", callback_data=f"{MENU_PREFIX}topics"
                ),
            ],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data=f"{MENU_PREFIX}help")],
        ]
    )


def _back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{MENU_PREFIX}main")]
        ]
    )


async def _show_menu(message: Message) -> None:
    try:
        user_id = message.from_user.id if message.from_user else None
        if user_id and user_id in MENU_MESSAGE_ID:
            menu_id = MENU_MESSAGE_ID[user_id]
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_id,
                text=MENU_TITLE,
                reply_markup=_main_menu_kb(),
            )
            return
    except Exception:
        logger.info("Menu edit failed, sending new message", exc_info=True)

    sent = await message.answer(MENU_TITLE, reply_markup=_main_menu_kb())
    if message.from_user:
        MENU_MESSAGE_ID[message.from_user.id] = sent.message_id


@router.message(Command("menu"))  # type: ignore
async def menu_command(message: Message) -> None:
    await _show_menu(message)
    try:
        await message.delete()
    except Exception:
        logger.debug("Menu command message delete failed", exc_info=True)


@router.callback_query(lambda c: c.data and c.data.startswith(MENU_PREFIX))  # type: ignore
async def menu_callback(callback: CallbackQuery) -> None:
    if not callback.message:
        return

    action = callback.data.split(":", 1)[1]
    if action == "main":
        await callback.message.edit_text(
            MENU_TITLE,
            reply_markup=_main_menu_kb(),
        )
        await callback.answer()
        return

    text = SECTION_TEXT.get(action, "Раздел недоступен.")

    await callback.message.edit_text(text, reply_markup=_back_kb())
    await callback.answer()
