from aiogram.fsm.state import StatesGroup, State


class AddTaskStates(StatesGroup):  # type: ignore
    waiting_for_title = State()
    waiting_for_due_at = State()
    waiting_for_priority = State()
    waiting_for_description = State()
    waiting_for_topic = State()
