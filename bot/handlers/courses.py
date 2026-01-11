import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
)

from bot.services.courses import create_course, fetch_courses
from bot.services.topics import fetch_topics
from bot.states.courses import AddCourseStates
from bot.utils.telegram_helpers import require_auth, send_message_with_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("add_course"))  # type: ignore
async def add_course_start(message: Message, state: FSMContext) -> None:
    token = await require_auth(message)
    if not token:
        return

    await state.clear()
    await message.answer("Введите название курса:")
    await state.set_state(AddCourseStates.waiting_for_title)


@router.message(AddCourseStates.waiting_for_title)  # type: ignore
async def add_course_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название курса не может быть пустым")
        return

    await state.update_data(title=title)
    await message.answer("Введите описание курса:")
    await state.set_state(AddCourseStates.waiting_for_description)


@router.message(AddCourseStates.waiting_for_description)  # type: ignore
async def add_course_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip() or None
    await state.update_data(description=description)

    data = await state.get_data()
    token = await require_auth(message)
    if not token:
        return

    success = await create_course(token, data["title"], data.get("description"))
    if success:
        await message.answer(f"📚 Курс «{data['title']}» успешно создан")
    else:
        await message.answer("❌ Ошибка создания курса")

    await state.clear()


@router.message(Command("courses"))  # type: ignore
async def list_courses_handler(message: Message) -> None:
    token = await require_auth(message)
    if not token:
        return

    courses = await fetch_courses(token)
    if not courses:
        await send_message_with_kb(message, "Нет курсов 😎")
        return

    for course in courses:
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
    token = await require_auth(query)
    if not token:
        return

    topics = await fetch_topics(token, course_id)
    if not topics:
        await send_message_with_kb(query.message, "Нет тем в этом курсе 😎")
        return

    for topic in topics:
        await send_message_with_kb(
            query.message,
            f"📘 <b>{topic['title']}</b>\n✅ Прогресс: {topic.get('progress', 0)}%",
            buttons=[
                {"text": "📝 Показать задачи", "callback": f"topic_tasks:{topic['id']}"}
            ],
        )
