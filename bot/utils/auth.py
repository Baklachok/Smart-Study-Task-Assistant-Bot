from aiogram.types import Message

from typing import Dict

# Хранилище токенов
user_tokens: Dict[int, str] = {}


def get_telegram_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


def get_access_token(message: Message) -> str | None:
    telegram_id = get_telegram_id(message)
    if telegram_id is None:
        return None
    return user_tokens.get(telegram_id)
