from aiogram.fsm.state import StatesGroup, State


class AddTopicStates(StatesGroup):  # type: ignore
    waiting_for_title = State()
    waiting_for_course = State()
