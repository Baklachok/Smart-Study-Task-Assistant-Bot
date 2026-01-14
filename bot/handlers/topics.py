import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
)

from bot.formatters.tasks import format_task
from bot.formatters.topics import format_topic
from bot.keyboards.topics import topic_kb, courses_kb
from bot.services.courses import fetch_courses
from bot.states.topics import AddTopicStates
from bot.utils.auth import get_access_token
from bot.utils.fsm_helpers import (
    CANCEL_TEXT,
    handle_cancel_message,
    handle_cancel_callback,
    cancel_kb,
    add_cancel_inline,
)
from bot.utils.http import post_entity, get_entities
from bot.utils.telegram_helpers import require_auth

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == CANCEL_TEXT)  # type: ignore
async def cancel_text_step(message: Message, state: FSMContext) -> None:
    await handle_cancel_message(message, state)


@router.callback_query(F.data == "cancel")  # type: ignore
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await handle_cancel_callback(callback, state)


@router.message(Command("add_topic"))  # type: ignore
async def add_topic_start(message: Message, state: FSMContext) -> None:
    if not await require_auth(message):
        return

    await state.clear()
    await message.answer("Введите название темы:", reply_markup=cancel_kb)
    await state.set_state(AddTopicStates.waiting_for_title)


@router.message(AddTopicStates.waiting_for_title)  # type: ignore
async def add_topic_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    user_id = message.from_user.id

    if not title:
        await message.answer(
            "Название не может быть пустым. Попробуйте ещё раз:", reply_markup=cancel_kb
        )
        logger.warning("User %s sent empty title", user_id)
        return

    await state.update_data(title=title)
    logger.info("User %s entered title: %r", user_id, title)

    token = await require_auth(message)
    if not token:
        logger.warning("User %s failed authentication", user_id)
        return

    courses = await fetch_courses(token)
    logger.info("Fetched %d courses for user %s", len(courses), user_id)

    await message.answer(
        "Выберите курс топика:",
        reply_markup=add_cancel_inline(courses_kb(courses)),
    )
    await state.set_state(AddTopicStates.waiting_for_course)


@router.callback_query(AddTopicStates.waiting_for_course)  # type: ignore
async def add_topic_course(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "cancel":
        await handle_cancel_callback(callback, state)
        return

    course_id = callback.data.split("course:")[-1]
    await state.update_data(course=course_id)
    await create_topic(callback, state)


async def create_topic(target: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    token = get_access_token(target)

    payload = {"title": data["title"], "course": data["course"]}

    status, _ = await post_entity("topics", token, payload)

    if status == 201:
        await target.answer(f"📘 Тема «{data['title']}» успешно создана")
    else:
        await target.answer("❌ Ошибка создания темы")

    await state.clear()


@router.message(Command("topics"))  # type: ignore
async def list_topics(message: Message) -> None:
    token = await require_auth(message)
    if not token:
        return

    status, topics = await get_entities("topics", token)
    if status != 200:
        await message.answer("Ошибка загрузки тем ❌")
        return

    if not topics:
        await message.answer("Тем пока нет 😎")
        return

    for topic in topics:
        await message.answer(
            format_topic(topic),
            reply_markup=topic_kb(topic["id"]),
            parse_mode="HTML",
        )


@router.callback_query(lambda c: c.data and c.data.startswith("topic_tasks:"))  # type: ignore
async def show_topic_tasks(query: CallbackQuery) -> None:
    topic_id = query.data.split(":", 1)[1]
    token = await require_auth(query)
    if not token:
        return

    status, tasks = await get_entities("tasks", token, params={"topic": topic_id})
    if status != 200:
        await query.message.answer("Ошибка загрузки задач ❌")
        return

    if not tasks:
        await query.message.answer("Нет задач в этой теме 😎")
        return

    for task in tasks:
        await query.message.answer(format_task(task), parse_mode="HTML")
