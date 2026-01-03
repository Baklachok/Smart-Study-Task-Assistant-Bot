from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.utils.auth import get_access_token
from bot.utils.http import api_client
from bot.utils.parsers import parse_add_course

router = Router()


@router.message(Command("add_course"))
async def add_course_handler(message: Message):
    if not message.text:
        await message.answer("Использование:\n/add_course Название | Описание")
        return

    access_token = get_access_token(message)
    if not access_token:
        await message.answer("Сначала /start")
        return

    try:
        title, description = parse_add_course(message.text)
    except Exception:
        await message.answer("Использование:\n/add_course Название | Описание")
        return

    payload = {"title": title}
    if description:
        payload["description"] = description

    headers = {"Authorization": f"Bearer {access_token}"}

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/courses/",
            headers=headers,
            json=payload,
        )

    if response.status_code == 201:
        await message.answer(f"📚 Курс «{title}» добавлен")
    else:
        await message.answer(f"Ошибка: {response.text}")
