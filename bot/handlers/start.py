import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..config import settings
from ..utils.auth import user_tokens, get_telegram_id
from ..utils.http import api_client

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    if not message.from_user:
        logger.warning("Start command without from_user")
        await message.answer("Ошибка: не удалось определить пользователя")
        return

    telegram_id = get_telegram_id(message)
    logger.info("Start auth telegram_id=%s", telegram_id)

    payload = {
        "telegram_id": telegram_id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "language": message.from_user.language_code or "en",
        "timezone": "UTC",
    }

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/users/telegram-login/",
            json=payload,
        )

    data = response.json()
    access_token = data.get("tokens", {}).get("access")
    if not access_token:
        logger.error("Auth failed telegram_id=%s response=%s", telegram_id, data)
        await message.answer("Ошибка авторизации ❌")
        return

    user_tokens[telegram_id] = access_token
    user = data["user"]
    created = data.get("created", False)

    logger.info(
        "User authenticated telegram_id=%s created=%s",
        telegram_id,
        created,
    )

    await message.answer(
        f"Привет, {user['first_name']}!\n"
        f"{'Регистрация завершена ✅' if created else 'С возвращением!'}"
    )
