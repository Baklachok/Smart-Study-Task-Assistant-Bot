from dataclasses import dataclass


@dataclass(frozen=True)
class CommandInfo:
    command: str
    description: str


COMMANDS: list[CommandInfo] = [
    CommandInfo("start", "Регистрация пользователя"),
    CommandInfo("add_task", "Создать задачу"),
    CommandInfo("tasks", "Список задач (today | week)"),
    CommandInfo("add_course", "Добавить курс"),
    CommandInfo("courses", "Список курсов"),
    CommandInfo("add_topic", "Добавить тему"),
    CommandInfo("topics", "Список тем"),
    CommandInfo("help", "Помощь"),
]
