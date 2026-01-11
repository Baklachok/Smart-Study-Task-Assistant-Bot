from typing import Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def task_actions_kb(task_id: int) -> InlineKeyboardMarkup:
    """
    Inline-кнопки для управления задачей
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Done",
                    callback_data=f"task_done:{task_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Delete",
                    callback_data=f"task_delete:{task_id}",
                ),
            ]
        ]
    )


def priority_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Low", callback_data="low"),
                InlineKeyboardButton(text="Medium", callback_data="medium"),
                InlineKeyboardButton(text="High", callback_data="high"),
            ]
        ]
    )


def topics_kb(topics: Any) -> InlineKeyboardMarkup:
    keyboard = []

    for topic in topics:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=topic["title"],
                    callback_data=f"topic:{topic['id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="Нет", callback_data="topic:none")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


skip_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_due_at")]
    ]
)

skip_description_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_description")]
    ]
)
