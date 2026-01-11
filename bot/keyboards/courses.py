from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def make_inline_kb(buttons: list[dict[str, str]]) -> InlineKeyboardMarkup:
    """Формирование inline-кнопок"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b["text"], callback_data=b["callback"])]
            for b in buttons
        ]
    )
