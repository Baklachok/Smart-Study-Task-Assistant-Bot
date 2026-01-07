import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from ..config import settings
from ..keyboards import task_actions_kb
from ..utils.http import api_client, task_api_request
from ..utils.parsers import parse_add_task, AddTaskParseError
from ..utils.telegram_helpers import extract_task_id, safe_edit_text, require_auth

logger = logging.getLogger(__name__)

router = Router()

PRIORITY_EMOJI = {
    "low": "🟢 low",
    "medium": "🟡 medium",
    "high": "🔴 high",
}


def _format_priority(priority: str | None) -> str:
    if priority is None:
        return "—"
    return PRIORITY_EMOJI.get(priority, "—")


def _format_due_at(due_at: str | None) -> str:
    if not due_at:
        return "—"
    try:
        dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return due_at


@router.message(Command("add_task"))
async def add_task_handler(message: Message):
    if not message.text:
        await message.answer("Использование: /add_task Название | дата | приоритет")
        return

    access_token = await require_auth(message)
    if not access_token:
        return

    try:
        title, due_at, priority = parse_add_task(message.text)
    except AddTaskParseError:
        logger.warning("Invalid add_task format: %s", message.text)
        await message.answer(
            "Использование:\n"
            "/add_task Название | [YYYY-MM-DD HH:MM] | [low|medium|high]"
        )
        return

    logger.info(
        "Creating task title=%r due_at=%s priority=%s",
        title,
        due_at,
        priority,
    )

    if priority and priority not in ("low", "medium", "high"):
        await message.answer("Приоритет: low | medium | high")
        return

    payload: dict[str, str] = {"title": title}
    if due_at:
        payload["due_at"] = due_at
    if priority:
        payload["priority"] = priority

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/tasks/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )

    if response.status_code == 201:
        logger.info("Task created successfully: %r", title)
        await message.answer(f"Задача «{title}» создана ✅")
        return
    logger.error(
        "Task creation failed status=%s response=%s",
        response.status_code,
        response.text,
    )
    await message.answer("Ошибка создания задачи ❌")


@router.message(Command("tasks"))
async def list_tasks_handler(message: Message):
    access_token = await require_auth(message)
    if not access_token:
        return

    text = (message.text or "").lower()
    if "today" in text:
        filter_type = "today"
    elif "week" in text:
        filter_type = "week"
    else:
        filter_type = None

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/tasks/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"filter": filter_type} if filter_type else {},
        )

    if response.status_code != 200:
        logger.error(
            "Failed to fetch tasks status=%s response=%s",
            response.status_code,
            response.text,
        )
        await message.answer("Ошибка загрузки задач ❌")
        return

    tasks = response.json().get("results", [])
    logger.info("Fetched %d tasks", len(tasks))

    if not tasks:
        await message.answer(
            "Нет задач 😎\n\n"
            "Подсказка:\n"
            "• /tasks today — задачи на сегодня\n"
            "• /tasks week — задачи на неделю"
        )
        return

    for task in tasks:
        task_text = (
            f"📝 <b>{task['title']}</b>\n"
            f"📄 {task.get('description') or '—'}\n"
            f"⏰ Дедлайн: {_format_due_at(task.get('due_at'))}\n"
            f"⚡ Приоритет: {_format_priority(task.get('priority'))}\n"
            f"📌 Статус: {task['status']}"
        )
        await message.answer(
            task_text,
            reply_markup=task_actions_kb(task["id"]),
            parse_mode="HTML",
        )


async def _handle_task_callback(
    callback: CallbackQuery, task_id: str | None, action: str, success_text: str
):
    access_token = await require_auth(callback)
    if not access_token or not task_id:
        return

    if action == "delete":
        method = "delete"
        payload = None
    elif action == "done":
        method = "patch"
        payload = {"status": "done"}
    else:
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


@router.callback_query(F.data.startswith("task_done:"))
async def task_done_callback(callback: CallbackQuery):
    task_id = extract_task_id(callback.data, "task_done:")
    await _handle_task_callback(callback, task_id, "done", "✅ Задача завершена")


@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_callback(callback: CallbackQuery):
    task_id = extract_task_id(callback.data, "task_delete:")
    await _handle_task_callback(callback, task_id, "delete", "❌ Задача удалена")
