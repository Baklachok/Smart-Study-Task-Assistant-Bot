from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def make_inline_kb(buttons: list[dict[str, str]]) -> InlineKeyboardMarkup:
    keyboard = []

    for b in buttons:
        callback_data = b.get("callback") or b.get("callback_data")
        if not callback_data:
            raise ValueError(f"Button must have 'callback' or 'callback_data': {b}")

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=b["text"],
                    callback_data=callback_data,
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
