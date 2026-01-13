import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from ..formatters.tasks import format_task
from ..keyboards import task_actions_kb
from ..keyboards.tasks import priority_kb, topics_kb, skip_kb, skip_description_kb
from ..services.tasks import create_task, fetch_tasks
from ..services.topics import fetch_topics
from ..states.tasks import AddTaskStates
from ..utils.http import task_api_request
from ..utils.telegram_helpers import extract_task_id, safe_edit_text, require_auth

logger = logging.getLogger(__name__)

router = Router()


async def prompt_topics(target: Message | CallbackQuery, state: FSMContext) -> None:
    """Показываем пользователю список топиков для выбора"""
    token = await require_auth(target)
    if not token:
        return

    topics = await fetch_topics(token)
    await target.answer(
        "Выберите топик задачи (или нажмите «Нет»):", reply_markup=topics_kb(topics)
    )
    await state.set_state(AddTaskStates.waiting_for_topic)


async def create_task_from_state(
    target: Message | CallbackQuery, state: FSMContext
) -> None:
    """Создание задачи через API на основе данных FSM"""
    token = await require_auth(target)
    if not token:
        return

    data = await state.get_data()
    topic_id = data.get("topic_id")

    payload = {
        "title": data["title"],
        "due_at": data.get("due_at"),
        "priority": data.get("priority"),
        "description": data.get("description"),
        **({"topic_id": topic_id} if topic_id else {}),
    }

    logger.info(
        "Creating task via API: payload=%s, user_id=%s",
        payload,
        getattr(target.from_user, "id", None),
    )

    response = await create_task(token, payload)
    if response.status_code == 201:
        await safe_edit_text(target.message, f"Задача «{data['title']}» создана ✅")
    else:
        await safe_edit_text(target.message, "Ошибка создания задачи ❌")

    await state.clear()
    await target.answer()


async def handle_task_action(
    callback: CallbackQuery, task_id: str | None, action: str, success_text: str
) -> None:
    access_token = await require_auth(callback)
    if not access_token or not task_id:
        return

    method, payload = {
        "delete": ("delete", None),
        "done": ("patch", {"status": "done"}),
    }.get(action, (None, None))

    if method is None:
        logger.error("Unknown action=%s", action)
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    response = await task_api_request(task_id, method, access_token, payload)

    if (action == "done" and response.status_code == 200) or (
        action == "delete" and response.status_code == 204
    ):
        logger.info("Task %s successfully task_id=%s", action, task_id)
        await safe_edit_text(callback.message, success_text)
        await callback.answer()
    else:
        logger.error(
            "Failed task %s task_id=%s status=%s", action, task_id, response.status_code
        )
        await callback.answer("Ошибка ❌", show_alert=True)


@router.message(Command("add_task"))  # type: ignore
async def add_task_handler(message: Message, state: FSMContext) -> None:
    access_token = await require_auth(message)
    if not access_token:
        return

    await message.answer("Введите название задачи:")
    await state.set_state(AddTaskStates.waiting_for_title)


@router.message(AddTaskStates.waiting_for_title)  # type: ignore
async def add_task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не может быть пустым. Введите название:")
        return
    await state.update_data(title=title)

    await message.answer(
        "Введите дедлайн в формате YYYY-MM-DD HH:MM или нажмите 'Пропустить':",
        reply_markup=skip_kb,
    )
    await state.set_state(AddTaskStates.waiting_for_due_at)


@router.message(AddTaskStates.waiting_for_due_at)  # type: ignore
async def add_task_due_at(message: Message, state: FSMContext) -> None:
    due_at_text = (message.text or "").strip()
    due_at_iso: str | None = None

    if due_at_text.lower() != "пропустить":
        try:
            due_at_iso = datetime.strptime(due_at_text, "%Y-%m-%d %H:%M").isoformat()
        except ValueError:
            await message.answer(
                "Неверный формат даты. Попробуйте ещё раз или нажмите 'Пропустить'."
            )
            return

    await state.update_data(due_at=due_at_iso)
    await message.answer("Выберите приоритет:", reply_markup=priority_kb())
    await state.set_state(AddTaskStates.waiting_for_priority)


@router.callback_query(AddTaskStates.waiting_for_due_at, F.data == "skip_due_at")  # type: ignore
async def skip_due_at_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(due_at=None)
    await callback.message.answer("Выберите приоритет:", reply_markup=priority_kb())
    await state.set_state(AddTaskStates.waiting_for_priority)
    await callback.answer()


@router.callback_query(AddTaskStates.waiting_for_priority)  # type: ignore
async def add_task_priority(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(priority=callback.data)
    await callback.message.answer(
        "Введите описание задачи или нажмите 'Пропустить':",
        reply_markup=skip_description_kb,
    )
    await state.set_state(AddTaskStates.waiting_for_description)
    await callback.answer()


@router.message(AddTaskStates.waiting_for_description)  # type: ignore
async def add_task_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip() or None)
    await prompt_topics(message, state)


@router.callback_query(
    AddTaskStates.waiting_for_description, F.data == "skip_description"
)  # type: ignore
async def skip_description_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await prompt_topics(callback, state)
    await callback.answer()


@router.callback_query(AddTaskStates.waiting_for_topic)  # type: ignore
async def add_task_topic(callback: CallbackQuery, state: FSMContext) -> None:
    topic_id = (
        None if callback.data == "topic:none" else callback.data.replace("topic:", "")
    )
    await state.update_data(topic_id=topic_id)
    await create_task_from_state(callback, state)


@router.message(Command("tasks"))  # type: ignore
async def list_tasks_handler(message: Message) -> None:
    access_token = await require_auth(message)
    if not access_token:
        return

    filter_type = (
        "today"
        if "today" in (message.text or "").lower()
        else "week"
        if "week" in (message.text or "").lower()
        else None
    )

    response = await fetch_tasks(access_token, filter_type)

    if response.status_code != 200:
        await message.answer("Ошибка загрузки задач ❌")
        return

    tasks = response.json().get("results", [])
    if not tasks:
        await message.answer("Нет задач 😎")
        return

    for task in tasks:
        await message.answer(
            format_task(task),
            reply_markup=task_actions_kb(task["id"]),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("task_done:"))  # type: ignore
async def task_done_callback(callback: CallbackQuery) -> None:
    task_id = extract_task_id(callback.data, "task_done:")
    await handle_task_action(callback, task_id, "done", "✅ Задача завершена")


@router.callback_query(F.data.startswith("task_delete:"))  # type: ignore
async def task_delete_callback(callback: CallbackQuery) -> None:
    task_id = extract_task_id(callback.data, "task_delete:")
    await handle_task_action(callback, task_id, "delete", "❌ Задача удалена")
