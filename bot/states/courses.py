from aiogram.fsm.state import StatesGroup, State


class AddCourseStates(StatesGroup):  # type: ignore
    waiting_for_title = State()
    waiting_for_description = State()
