import logging
from typing import Dict

from aiogram.types import Message

logger = logging.getLogger(__name__)

# Хранилище токенов
user_tokens: Dict[int, str] = {}


def get_telegram_id(obj: Message) -> int:
    """
    Унифицированное получение telegram_id
    """
    if hasattr(obj, "from_user") and obj.from_user:
        telegram_id = int(obj.from_user.id)
        logger.debug("Got telegram_id=%s from message object", telegram_id)
        return telegram_id

    if hasattr(obj, "message") and obj.message and obj.message.from_user:
        telegram_id = int(obj.message.from_user.id)
        logger.debug("Got telegram_id=%s from callback object", telegram_id)
        return telegram_id

    logger.error("Cannot determine telegram_id from object: %s", obj)
    raise RuntimeError("Cannot determine telegram_id")


def get_access_token(obj: Message) -> str | None:
    telegram_id = get_telegram_id(obj)
    token = user_tokens.get(telegram_id)
    if token:
        logger.debug("Access token found for telegram_id=%s", telegram_id)
    else:
        logger.warning("Access token not found for telegram_id=%s", telegram_id)
    return token
