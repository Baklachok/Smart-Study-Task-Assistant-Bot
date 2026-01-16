import logging
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


async def guard_callback(
    callback: CallbackQuery,
    state: FSMContext,
    allowed_prefixes: set[str],
) -> bool:
    """
    Блокирует callback, если он не относится к текущему FSM шагу
    """
    data = callback.data or ""
    current_state = await state.get_state()

    if not any(data.startswith(prefix) for prefix in allowed_prefixes):
        logger.warning(
            "Blocked callback '%s' in state '%s'",
            data,
            current_state,
        )
        await callback.answer(
            "Эта кнопка больше не активна ❌",
            show_alert=True,
        )
        return False

    return True
