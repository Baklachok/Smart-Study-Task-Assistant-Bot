import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.filters import Command
from ..config import settings
from ..keyboards import task_actions_kb
from ..utils.auth import user_tokens, get_telegram_id
from ..utils.formatters import format_due_at, format_priority
from ..utils.http import api_client, task_api_request
from ..utils.parsers import parse_add_task, AddTaskParseError
from ..utils.telegram_helpers import extract_task_id, safe_edit_text, require_auth

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    if message.from_user is None:
        logger.warning("Start command without from_user")
        await message.answer("Ошибка: не удалось определить пользователя")
        return

    telegram_id = get_telegram_id(message)
    logger.info("Start auth for telegram_id=%s", telegram_id)

    payload = {
        "telegram_id": telegram_id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "language": message.from_user.language_code or "en",
        "timezone": "UTC",
    }

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/users/telegram-login/",
            json=payload,
        )

    data = response.json()
    access_token = data.get("tokens", {}).get("access")

    if not access_token:
        logger.error("Auth failed for telegram_id=%s: no access token", telegram_id)
        await message.answer("Ошибка авторизации")
        return

    user_tokens[telegram_id] = access_token

    user = data["user"]
    created = data.get("created", False)
    logger.info(
        "User authenticated telegram_id=%s created=%s",
        telegram_id,
        created,
    )

    await message.answer(
        f"Привет, {user['first_name']}!\n"
        + ("Регистрация завершена ✅" if created else "С возвращением!")
    )


@router.message(Command("add_task"))
async def add_task_handler(message: Message):
    if not message.text:
        await message.answer("Использование: /add_task Название | дата | приоритет")
        return

    access_token = await require_auth(message)
    if not access_token:
        logger.warning("Add task without auth")
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
    else:
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
        logger.warning("Tasks list requested without auth")
        return

    text = (message.text or "").lower()
    filter_type = "today" if "today" in text else "week" if "week" in text else None

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

    tasks = response.json()
    logger.info("Fetched %d tasks", len(tasks))
    if not tasks:
        await message.answer("Нет задач 😎")
        return

    for task in tasks:
        await message.answer(
            (
                f"📝 <b>{task['title']}</b>\n"
                f"📄 {task.get('description') or '—'}\n"
                f"⏰ Дедлайн: {format_due_at(task.get('due_at'))}\n"
                f"⚡ Приоритет: {format_priority(task.get('priority'))}\n"
                f"📌 Статус: {task['status']}"
            ),
            reply_markup=task_actions_kb(task["id"]),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("task_done:"))
async def task_done_callback(callback: CallbackQuery):
    access_token = await require_auth(callback)
    if not access_token or not callback.data:
        logger.warning("Task done callback without auth or data")
        return

    task_id = extract_task_id(callback.data, "task_done:")
    if not task_id:
        logger.warning("Invalid task_done callback data=%s", callback.data)
        await callback.answer("Ошибка данных", show_alert=True)
        return

    logger.info("Marking task done task_id=%s", task_id)

    response = await task_api_request(
        task_id, "patch", access_token, {"status": "done"}
    )

    if response.status_code == 200:
        logger.info("Task marked done task_id=%s", task_id)
        await safe_edit_text(callback.message, "✅ Задача завершена")
        await callback.answer()
    else:
        logger.error(
            "Failed to mark task done task_id=%s status=%s",
            task_id,
            response.status_code,
        )
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_callback(callback: CallbackQuery):
    access_token = await require_auth(callback)
    if not access_token or not callback.data:
        logger.warning("Task delete callback without auth or data")
        return

    task_id = extract_task_id(callback.data, "task_delete:")
    if not task_id:
        logger.warning("Invalid task_delete callback data=%s", callback.data)
        await callback.answer("Ошибка данных", show_alert=True)
        return

    logger.info("Marking task delete task_id=%s", task_id)

    response = await task_api_request(task_id, "delete", access_token)

    if response.status_code == 204:
        logger.info("Task deleted task_id=%s", task_id)
        await safe_edit_text(callback.message, "❌ Задача удалена")
        await callback.answer()
    else:
        logger.error(
            "Failed to deleted task_id=%s status=%s",
            task_id,
            response.status_code,
        )
        await callback.answer("Ошибка удаления", show_alert=True)
