from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..config import settings
from ..utils.auth import user_tokens, get_access_token
from ..utils.http import api_client
from ..utils.parsers import parse_add_task

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    if message.from_user is None:
        await message.answer("Ошибка: не удалось определить пользователя")
        return

    telegram_id = message.from_user.id

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
        await message.answer("Ошибка авторизации")
        return

    user_tokens[telegram_id] = access_token

    user = data["user"]
    created = data.get("created", False)

    await message.answer(
        f"Привет, {user['first_name']}!\n"
        + ("Регистрация завершена ✅" if created else "С возвращением!")
    )


@router.message(Command("add_task"))
async def add_task_handler(message: Message):
    if not message.text:
        await message.answer("Использование: /add_task Название | дата | приоритет")
        return

    access_token = get_access_token(message)
    if not access_token:
        await message.answer("Сначала авторизуйтесь через /start")
        return

    try:
        title, due_at, priority = parse_add_task(message.text)
    except Exception:
        await message.answer(
            "Использование:\n/add_task Название | [YYYY-MM-DD HH:MM] | [low|medium|high]"
        )
        return

    if priority and priority not in ("low", "medium", "high"):
        await message.answer("Приоритет: low | medium | high")
        return

    payload = {"title": title}
    if due_at:
        payload["due_at"] = due_at
    if priority:
        payload["priority"] = priority

    headers = {"Authorization": f"Bearer {access_token}"}

    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/tasks/",
            headers=headers,
            json=payload,
        )

    if response.status_code == 201:
        await message.answer(f"Задача «{title}» создана ✅")
    else:
        await message.answer(f"Ошибка: {response.text}")


@router.message(Command("tasks"))
async def list_tasks_handler(message: Message):
    if not message.text:
        return

    access_token = get_access_token(message)
    if not access_token:
        await message.answer("Сначала авторизуйтесь через /start")
        return

    text = message.text.lower()
    filter_type = "today" if "today" in text else "week" if "week" in text else None

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"filter": filter_type} if filter_type else {}

    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/tasks/",
            headers=headers,
            params=params,
        )

    if response.status_code != 200:
        await message.answer(f"Ошибка: {response.text}")
        return

    tasks = response.json()
    if not tasks:
        await message.answer("Нет задач 😎")
        return

    await message.answer(
        "\n".join(f"{t['id']} — {t['title']} ({t['status']})" for t in tasks)
    )


@router.message(Command("done"))
async def done_task_handler(message: Message):
    if not message.text:
        await message.answer("Использование: /done <task_id>")
        return

    access_token = get_access_token(message)
    if not access_token:
        await message.answer("Сначала авторизуйтесь через /start")
        return

    try:
        _, task_id = message.text.split(" ", 1)
    except ValueError:
        await message.answer("Использование: /done <task_id>")
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    async with api_client() as client:
        response = await client.patch(
            f"{settings.API_URL}/tasks/{task_id}/",
            headers=headers,
            json={"status": "done"},
        )

    if response.status_code == 200:
        await message.answer("Задача завершена ✅")
    else:
        await message.answer(f"Ошибка: {response.text}")
