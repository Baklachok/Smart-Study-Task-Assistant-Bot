from typing import Any

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


def courses_kb(courses: Any) -> InlineKeyboardMarkup:
    keyboard = []

    for course in courses:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=course["title"],
                    callback_data=f"course:{course['id']}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
