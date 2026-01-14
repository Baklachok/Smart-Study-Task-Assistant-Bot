import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.services.courses import create_course, fetch_courses
from bot.services.topics import fetch_topics
from bot.states.courses import AddCourseStates
from bot.utils.fsm_helpers import (
    CANCEL_TEXT,
    handle_cancel_message,
    handle_cancel_callback,
    cancel_kb,
    add_cancel_inline,
)
from bot.utils.telegram_helpers import require_auth, send_message_with_kb

logger = logging.getLogger(__name__)
router = Router()


# ====================
# Отмена действий
# ====================
@router.message(F.text == CANCEL_TEXT)  # type: ignore
async def cancel_text_step(message: Message, state: FSMContext) -> None:
    """Отмена через текстовое сообщение"""
    await handle_cancel_message(message, state)


@router.callback_query(F.data == "cancel")  # type: ignore
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена через inline кнопку"""
    await handle_cancel_callback(callback, state)


# ====================
# Создание курса
# ====================
@router.message(Command("add_course"))  # type: ignore
async def add_course_start(message: Message, state: FSMContext) -> None:
    """Начало создания курса"""
    token = await require_auth(message)
    if not token:
        return

    await state.clear()
    await message.answer("Введите название курса:", reply_markup=cancel_kb)
    await state.set_state(AddCourseStates.waiting_for_title)


@router.message(AddCourseStates.waiting_for_title)  # type: ignore
async def add_course_title(message: Message, state: FSMContext) -> None:
    """Сохраняем название курса"""
    title = (message.text or "").strip()
    if not title:
        await message.answer(
            "Название курса не может быть пустым", reply_markup=cancel_kb
        )
        return

    await state.update_data(title=title)
    await message.answer("Введите описание курса:", reply_markup=cancel_kb)
    await state.set_state(AddCourseStates.waiting_for_description)


@router.message(AddCourseStates.waiting_for_description)  # type: ignore
async def add_course_description(message: Message, state: FSMContext) -> None:
    """Сохраняем описание и создаем курс через API"""
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


# ====================
# Просмотр курсов
# ====================
def build_course_buttons(course_id: str) -> list[dict[str, str]]:
    """Создание кнопок для курса"""
    return [{"text": "📘 Показать темы", "callback_data": f"course_topics:{course_id}"}]


def build_topic_buttons(topic_id: str) -> list[dict[str, str]]:
    """Создание кнопок для темы"""
    return [
        {"text": "📝 Показать задачи", "callback_data": f"topic_tasks:{topic_id}"},
        {"text": "❌ Отмена", "callback_data": "cancel"},
    ]


@router.message(Command("courses"))  # type: ignore
async def list_courses_handler(message: Message) -> None:
    """Листинг всех курсов"""
    token = await require_auth(message)
    if not token:
        return

    courses = await fetch_courses(token)
    if not courses:
        await send_message_with_kb(message, "Нет курсов 😎")
        return

    for course in courses:
        buttons = build_course_buttons(course["id"])
        final_kb = add_cancel_inline(buttons)
        await send_message_with_kb(
            message,
            f"📚 <b>{course['title']}</b>\n📄 {course.get('description', '—')}",
            buttons=final_kb,
        )


# ====================
# Просмотр тем курса
# ====================
@router.callback_query(lambda c: c.data and c.data.startswith("course_topics:"))  # type: ignore
async def show_course_topics(query: CallbackQuery) -> None:
    """Показываем темы конкретного курса"""
    if query.data == "cancel":
        await query.message.edit_text("Действие отменено ❌")
        await query.answer()
        return

    course_id = query.data.split(":")[1]
    token = await require_auth(query)
    if not token:
        return

    topics = await fetch_topics(token, course_id)
    if not topics:
        await send_message_with_kb(query.message, "Нет тем в этом курсе 😎")
        return

    for topic in topics:
        buttons = build_topic_buttons(topic["id"])
        await send_message_with_kb(
            query.message,
            f"📘 <b>{topic['title']}</b>\n✅ Прогресс: {topic.get('progress', 0)}%",
            buttons=buttons,
        )
