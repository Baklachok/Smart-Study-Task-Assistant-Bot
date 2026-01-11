from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def topic_kb(topic_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Показать задачи",
                    callback_data=f"topic_tasks:{topic_id}",
                )
            ]
        ]
    )
