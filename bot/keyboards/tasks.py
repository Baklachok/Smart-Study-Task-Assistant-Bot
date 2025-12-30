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
