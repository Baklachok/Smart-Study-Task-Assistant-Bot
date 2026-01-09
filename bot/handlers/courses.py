import logging
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from bot.config import settings
from bot.utils.auth import get_access_token, get_telegram_id
from bot.utils.http import api_client
from bot.utils.parsers import parse_add_course


logger = logging.getLogger(__name__)
router = Router()


def make_inline_kb(buttons: list[dict[str, str]]) -> InlineKeyboardMarkup:
    """Формирование inline-кнопок"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b["text"], callback_data=b["callback"])]
            for b in buttons
        ]
    )


async def send_message_with_kb(
    message_obj: Any, text: str, buttons: list[dict[str, str]] | None = None
) -> None:
    """Отправка сообщения с опциональными кнопками"""
    kb = make_inline_kb(buttons) if buttons else None
    await message_obj.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("add_course"))  # type: ignore
async def add_course_handler(message: Message) -> None:
    user_id = get_telegram_id(message)
    logger.info("Command /add_course received from user %s", user_id)

    if not message.text:
        await send_message_with_kb(
            message, "Использование:\n/add_course Название | Описание"
        )
        return

    token = get_access_token(message)
    if not token:
        await send_message_with_kb(message, "Сначала /start")
        return

    try:
        title, description = parse_add_course(message.text)
    except (ValueError, IndexError) as e:
        logger.error("Failed to parse /add_course message: %s", e)
        await send_message_with_kb(
            message, "Использование:\n/add_course Название | Описание"
        )
        return

    payload = {"title": title}
    if description:
        payload["description"] = description

    headers = {"Authorization": f"Bearer {token}"}
    logger.debug("Sending POST request to /courses/ with payload=%s", payload)

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/courses/", headers=headers, json=payload
        )

    logger.info("POST /courses/ responded with status %s", response.status_code)
    if response.status_code == 201:
        await send_message_with_kb(message, f"📚 Курс «{title}» добавлен")
    else:
        await send_message_with_kb(message, f"Ошибка: {response.text}")
    logger.info("POST /courses/ responded with status %s", response.status_code)
    if response.status_code == 201:
        await message.answer(f"📚 Курс «{title}» добавлен")
    else:
        await message.answer(f"Ошибка: {response.text}")


@router.message(Command("courses"))  # type: ignore
async def list_courses_handler(message: Message) -> None:
    user_id = get_telegram_id(message)
    logger.info("Command /courses received from user %s", user_id)

    token = get_access_token(message)
    if not token:
        await send_message_with_kb(message, "Сначала /start")
        return

    logger.debug("Fetching courses from API")
    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/courses/", headers={"Authorization": f"Bearer {token}"}
        )

    logger.info("GET /courses/ responded with status %s", response.status_code)
    if response.status_code != 200:
        await send_message_with_kb(message, "Ошибка загрузки курсов ❌")
        return

    courses = response.json().get("results", [])
    if not courses:
        await send_message_with_kb(message, "Нет курсов 😎")
        return

    for course in courses:
        logger.debug("Sending course info to user: %s", course)
        await send_message_with_kb(
            message,
            f"📚 <b>{course['title']}</b>\n📄 {course.get('description', '—')}",
            buttons=[
                {
                    "text": "📘 Показать темы",
                    "callback": f"course_topics:{course['id']}",
                }
            ],
        )


@router.callback_query(lambda c: c.data and c.data.startswith("course_topics:"))  # type: ignore
async def show_course_topics(query: CallbackQuery) -> None:
    course_id = query.data.split(":")[1]
    user_id = get_telegram_id(query)
    logger.info(
        "Callback query to show topics for course %s from user %s",
        course_id,
        user_id,
    )

    token = get_access_token(query)
    if not token:
        await send_message_with_kb(query.message, "Сначала /start")
        return

    logger.debug("Fetching topics for course %s from API", course_id)
    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/topics/",
            headers={"Authorization": f"Bearer {token}"},
            params={"course": course_id},
        )

    logger.info(
        "GET /topics/ for course %s responded with status %s",
        course_id,
        response.status_code,
    )
    if response.status_code != 200:
        await send_message_with_kb(query.message, "Ошибка загрузки тем ❌")
        return

    topics = response.json().get("results", [])
    if not topics:
        await send_message_with_kb(query.message, "Нет тем в этом курсе 😎")
        return

    for topic in topics:
        logger.debug("Sending topic info to user: %s", topic)
        await send_message_with_kb(
            query.message,
            f"📘 <b>{topic['title']}</b>\n✅ Прогресс: {topic.get('progress', 0)}%",
            buttons=[
                {"text": "📝 Показать задачи", "callback": f"topic_tasks:{topic['id']}"}
            ],
        )
