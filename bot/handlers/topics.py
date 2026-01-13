import logging
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
)

from bot.config import settings
from bot.keyboards.topics import topic_kb, courses_kb
from bot.services.courses import fetch_courses
from bot.states.topics import AddTopicStates
from bot.utils.auth import get_access_token
from bot.utils.http import api_client
from bot.utils.telegram_helpers import require_auth

logger = logging.getLogger(__name__)

router = Router()


def auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@router.message(Command("add_topic"))  # type: ignore
async def add_topic_start(message: Message, state: FSMContext) -> None:
    if not await require_auth(message):
        return

    await state.clear()
    await message.answer("Введите название темы:")
    await state.set_state(AddTopicStates.waiting_for_title)


@router.message(AddTopicStates.waiting_for_title)  # type: ignore
async def add_topic_title(message: Message, state: FSMContext) -> None:
    """Получение названия темы от пользователя"""
    title = (message.text or "").strip()
    user_id = message.from_user.id

    if not title:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        logger.warning("User %s sent empty title", user_id)
        return

    await state.update_data(title=title)
    logger.info("User %s entered title: %r", user_id, title)

    token = await require_auth(message)
    if not token:
        logger.warning("User %s failed authentication", user_id)
        return
    logger.debug("User %s authenticated successfully", user_id)

    courses = await fetch_courses(token)
    logger.info("Fetched %d courses for user %s", len(courses), user_id)

    await message.answer(
        "Выберите курс топика:",
        reply_markup=courses_kb(courses),
    )
    await state.set_state(AddTopicStates.waiting_for_course)


@router.callback_query(AddTopicStates.waiting_for_course)  # type: ignore
async def add_topic_course(callback: CallbackQuery, state: FSMContext) -> None:
    course_uid = callback.data.replace("course:", "")

    await state.update_data(course=course_uid)
    await create_topic(callback, state)


async def create_topic(
    target: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    token = get_access_token(target)

    payload = {
        "title": data["title"],
        "course": data["course"],
    }

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/topics/",
            headers=auth_headers(token),
            json=payload,
        )

    if response.status_code == 201:
        await target.answer(f"📘 Тема «{data['title']}» успешно создана")
    else:
        await target.answer(f"❌ Ошибка создания темы:\n{response.text}")

    await state.clear()


@router.message(Command("topics"))  # type: ignore
async def list_topics(message: Message) -> None:
    token = await require_auth(message)
    if not token:
        return

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/topics/",
            headers=auth_headers(token),
        )

    if response.status_code != 200:
        await message.answer("Ошибка загрузки тем ❌")
        return

    topics = response.json().get("results", [])
    if not topics:
        await message.answer("Тем пока нет 😎")
        return

    for topic in topics:
        await message.answer(
            format_topic(topic),
            reply_markup=topic_kb(topic["id"]),
            parse_mode="HTML",
        )


def format_topic(topic: dict[str, Any]) -> str:
    return (
        f"📘 <b>{topic['title']}</b>\n"
        f"📚 Курс: {topic.get('course_name', 'Без курса')}\n"
        f"✅ Прогресс: {topic.get('progress', 0)}%"
    )


@router.callback_query(lambda c: c.data and c.data.startswith("topic_tasks:"))  # type: ignore
async def show_topic_tasks(query: CallbackQuery) -> None:
    topic_id = query.data.split(":", 1)[1]

    token = await require_auth(query)
    if not token:
        return

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/tasks/",
            headers=auth_headers(token),
            params={"topic": topic_id},
        )

    if response.status_code != 200:
        await query.message.answer("Ошибка загрузки задач ❌")
        return

    tasks = response.json().get("results", [])
    if not tasks:
        await query.message.answer("Нет задач в этой теме 😎")
        return

    for task in tasks:
        await query.message.answer(format_task(task), parse_mode="HTML")


def format_task(task: dict[str, Any]) -> str:
    return (
        f"📝 <b>{task['title']}</b>\n"
        f"📄 {task.get('description') or '—'}\n"
        f"⏰ Дедлайн: {task.get('due_at') or '—'}\n"
        f"⚡ Приоритет: {task.get('priority') or '—'}\n"
        f"📌 Статус: {task.get('status') or '—'}"
    )
