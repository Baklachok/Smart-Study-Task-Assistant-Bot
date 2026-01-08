from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.utils.auth import get_access_token
from bot.utils.http import api_client
from bot.utils.parsers import parse_add_topic

router = Router()


@router.message(Command("add_topic"))  # type: ignore
async def add_topic_handler(message: Message) -> None:
    if not message.text:
        await message.answer("Использование:\n/add_topic Title | course_id")
        return

    token = get_access_token(message)
    if not token:
        await message.answer("Сначала /start")
        return

    try:
        title, course_id = parse_add_topic(message.text)
    except Exception:
        await message.answer("Использование:\n/add_topic Title | course_id")
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "course": course_id,
    }

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/topics/",
            headers=headers,
            json=payload,
        )

    if response.status_code == 201:
        await message.answer(f"📘 Тема «{title}» добавлена")
    else:
        await message.answer(f"Ошибка: {response.text}")
