import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.tasks import skip_kb, priority_kb, skip_description_kb
from bot.services.topics import fetch_topics
from bot.states.tasks import AddTaskStates
from bot.utils.telegram_helpers import (
    with_cancel,
    send_message_with_kb,
    normalize_buttons,
    require_auth,
    CANCEL_BUTTON,
)

logger = logging.getLogger(__name__)


async def ask_due_at(target: Message | CallbackQuery) -> None:
    buttons = with_cancel(
        normalize_buttons(
            [
                (btn.text, btn.callback_data)
                for row in skip_kb.inline_keyboard
                for btn in row
            ]
        )
    )
    await send_message_with_kb(
        target,
        "Введите дедлайн (YYYY-MM-DD HH:MM) или нажмите «Пропустить»:",
        buttons=buttons,
    )


async def ask_priority(target: Message | CallbackQuery) -> None:
    buttons = with_cancel(
        normalize_buttons(
            [
                (btn.text, btn.callback_data)
                for row in priority_kb().inline_keyboard
                for btn in row
            ]
        )
    )
    await send_message_with_kb(target, "Выберите приоритет:", buttons=buttons)


async def ask_description(target: Message | CallbackQuery) -> None:
    buttons = with_cancel(
        normalize_buttons(
            [
                (btn.text, btn.callback_data)
                for row in skip_description_kb.inline_keyboard
                for btn in row
            ]
        )
    )
    await send_message_with_kb(
        target, "Введите описание или нажмите «Пропустить»:", buttons=buttons
    )


async def prompt_topics(target: Message | CallbackQuery, state: FSMContext) -> None:
    logger.debug("Prompting topics")

    token = await require_auth(target)
    if not token:
        return

    topics = await fetch_topics(token)
    logger.debug("Fetched %d topics", len(topics))

    buttons = [
        {"text": t["title"], "callback_data": f"topic:{t['id']}"} for t in topics
    ] + [
        {"text": "Нет", "callback_data": "topic:none"},
        CANCEL_BUTTON,
    ]

    await send_message_with_kb(
        target,
        "Выберите топик задачи (или нажмите «Нет»):",
        buttons=buttons,
    )

    await state.set_state(AddTaskStates.waiting_for_topic)
