import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from .tasks_helpers import ask_due_at, ask_priority, ask_description, prompt_topics
from ..formatters.tasks import format_task
from ..keyboards import task_actions_kb
from ..services.tasks import create_task, fetch_tasks
from ..states.tasks import AddTaskStates
from ..utils.fsm_guard import guard_callback
from ..utils.fsm_helpers import (
    CANCEL_TEXT,
    handle_cancel_message,
    handle_cancel_callback,
    cancel_kb,
    perform_task_action,
)
from ..utils.telegram_helpers import (
    extract_task_id,
    require_auth,
    send_message_with_kb,
    normalize_buttons,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == CANCEL_TEXT)  # type: ignore
async def cancel_text_step(message: Message, state: FSMContext) -> None:
    logger.info("Cancel via text by user %s", message.from_user.id)
    await handle_cancel_message(message, state)


@router.callback_query(F.data == "cancel")  # type: ignore
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("Cancel via callback by user %s", callback.from_user.id)
    await handle_cancel_callback(callback, state)


async def create_task_from_state(
    target: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    token = await require_auth(target)
    if not token:
        return

    data = await state.get_data()
    logger.debug("FSM data for task creation: %s", data)

    payload = {
        "title": data["title"],
        "due_at": data.get("due_at"),
        "priority": data.get("priority"),
        "description": data.get("description"),
        **({"topic_id": data["topic_id"]} if data.get("topic_id") else {}),
    }

    logger.info("Creating task: %s", payload)
    response = await create_task(token, payload)

    if response.status_code == 201:
        await send_message_with_kb(
            target,
            f"Задача «{data['title']}» создана ✅",
        )
    else:
        logger.error(
            "Task creation failed: %s %s",
            response.status_code,
            response.text,
        )
        await send_message_with_kb(target, "Ошибка создания задачи ❌")

    await state.clear()


@router.message(Command("add_task"))  # type: ignore
async def add_task_handler(message: Message, state: FSMContext) -> None:
    logger.info("User %s started add_task", message.from_user.id)

    if not await require_auth(message):
        return

    await state.clear()
    await message.answer("Введите название задачи:", reply_markup=cancel_kb)
    await state.set_state(AddTaskStates.waiting_for_title)


@router.message(AddTaskStates.waiting_for_title)  # type: ignore
async def add_task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не может быть пустым", reply_markup=cancel_kb)
        return

    await state.update_data(title=title)
    await ask_due_at(message)
    await state.set_state(AddTaskStates.waiting_for_due_at)


@router.message(AddTaskStates.waiting_for_due_at)  # type: ignore
async def add_task_due_at(message: Message, state: FSMContext) -> None:
    due_text = (message.text or "").strip()
    if due_text.lower() == "пропустить":
        await state.update_data(due_at=None)
    else:
        try:
            due_iso = datetime.strptime(due_text, "%Y-%m-%d %H:%M").isoformat()
            await state.update_data(due_at=due_iso)
        except ValueError:
            await message.answer(
                "Неверный формат даты. Используйте: YYYY-MM-DD HH:MM\nИли нажмите «Пропустить» кнопкой 👇"
            )
            return

    await ask_priority(message)
    await state.set_state(AddTaskStates.waiting_for_priority)


@router.callback_query(AddTaskStates.waiting_for_due_at)  # type: ignore
async def skip_due_at_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data != "skip_due_at":
        return

    await state.update_data(due_at=None)
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_priority(callback)
    await state.set_state(AddTaskStates.waiting_for_priority)
    await callback.answer()


@router.callback_query(AddTaskStates.waiting_for_priority)  # type: ignore
async def add_task_priority(callback: CallbackQuery, state: FSMContext) -> None:
    if not await guard_callback(callback, state, {"priority:", "cancel"}):
        return

    await state.update_data(priority=callback.data.split(":", 1)[1])

    await callback.message.edit_reply_markup(reply_markup=None)

    await ask_description(callback)
    await state.set_state(AddTaskStates.waiting_for_description)
    await callback.answer()


@router.message(AddTaskStates.waiting_for_description)  # type: ignore
async def add_task_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip() or None)
    await prompt_topics(message, state)


@router.callback_query(AddTaskStates.waiting_for_description)  # type: ignore
async def skip_description_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not await guard_callback(callback, state, {"skip_description", "cancel"}):
        return

    await state.update_data(description=None)
    await callback.message.edit_reply_markup(reply_markup=None)
    await prompt_topics(callback, state)
    await callback.answer()


@router.callback_query(AddTaskStates.waiting_for_topic)  # type: ignore
async def add_task_topic(callback: CallbackQuery, state: FSMContext) -> None:
    if not await guard_callback(callback, state, {"topic:", "cancel"}):
        return

    topic_id = None if callback.data == "topic:none" else callback.data[6:]
    await state.update_data(topic_id=topic_id)

    await callback.message.edit_reply_markup(reply_markup=None)
    await create_task_from_state(callback, state)


@router.message(Command("tasks"))  # type: ignore
async def list_tasks_handler(message: Message) -> None:
    token = await require_auth(message)
    if not token:
        return

    response = await fetch_tasks(token, None)
    if response.status_code != 200:
        await send_message_with_kb(message, "Ошибка загрузки задач ❌")
        return

    tasks = response.json().get("results", [])
    if not tasks:
        await send_message_with_kb(message, "Нет задач 😎")
        return

    for task in tasks:
        buttons = normalize_buttons(
            [
                (btn.text, btn.callback_data)
                for row in task_actions_kb(task["id"]).inline_keyboard
                for btn in row
            ]
        )
        await send_message_with_kb(
            message,
            format_task(task),
            buttons=buttons,
        )


@router.callback_query(F.data.startswith("task_done:"))  # type: ignore
async def task_done_callback(callback: CallbackQuery) -> None:
    task_id = extract_task_id(callback.data, "task_done:")
    await perform_task_action(callback, task_id, "done", "✅ Задача завершена")


@router.callback_query(F.data.startswith("task_delete:"))  # type: ignore
async def task_delete_callback(callback: CallbackQuery) -> None:
    task_id = extract_task_id(callback.data, "task_delete:")
    await perform_task_action(callback, task_id, "delete", "❌ Задача удалена")
