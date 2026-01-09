from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.config import settings
from bot.utils.auth import get_access_token
from bot.utils.http import api_client
from bot.utils.parsers import parse_add_topic

router = Router()


async def _require_token(message_or_query: Any) -> str | None:
    token = get_access_token(message_or_query)
    if not token:
        await getattr(message_or_query, "answer")("Сначала /start")
    return token


@router.message(Command("add_topic"))  # type: ignore
async def add_topic_handler(message: Message) -> None:
    """Добавление новой темы"""
    if not message.text:
        await message.answer("Использование:\n/add_topic Title | course_id")
        return

    token = await _require_token(message)
    if not token:
        return

    try:
        title, course_id = parse_add_topic(message.text)
    except (ValueError, IndexError):
        await message.answer("Использование:\n/add_topic Title | course_id")
        return

    payload = {"title": title, "course": course_id}
    headers = {"Authorization": f"Bearer {token}"}

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/topics/", headers=headers, json=payload
        )

    if response.status_code == 201:
        await message.answer(f"📘 Тема «{title}» добавлена")
    else:
        await message.answer(f"Ошибка: {response.text}")


@router.message(Command("topics"))  # type: ignore
async def list_topics_handler(message: Message) -> None:
    """Вывод списка тем с кнопками для просмотра задач"""
    token = await _require_token(message)
    if not token:
        return

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/topics/", headers={"Authorization": f"Bearer {token}"}
        )

    if response.status_code != 200:
        await message.answer("Ошибка загрузки тем ❌")
        return

    topics = response.json().get("results", [])
    if not topics:
        await message.answer("Тем пока нет 😎")
        return

    for topic in topics:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📘 Показать задачи",
                        callback_data=f"topic_tasks:{topic['id']}",
                    )
                ]
            ]
        )

        topic_text = (
            f"📘 <b>{topic['title']}</b>\n"
            f"📚 Курс: {topic.get('course_name', 'Без курса')}\n"
            f"✅ Прогресс: {topic.get('progress', 0)}%"
        )

        await message.answer(topic_text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(lambda c: c.data and c.data.startswith("topic_tasks:"))  # type: ignore
async def show_topic_tasks(query: CallbackQuery) -> None:
    """Показать задачи конкретной темы"""
    topic_id = query.data.split(":")[1]

    token = await _require_token(query)
    if not token:
        return

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/tasks/",
            headers={"Authorization": f"Bearer {token}"},
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
        task_text = (
            f"📝 <b>{task['title']}</b>\n"
            f"📄 {task.get('description') or '—'}\n"
            f"⏰ Дедлайн: {task.get('due_at') or '—'}\n"
            f"⚡ Приоритет: {task.get('priority') or '—'}\n"
            f"📌 Статус: {task.get('status') or '—'}"
        )
        await query.message.answer(task_text, parse_mode="HTML")
