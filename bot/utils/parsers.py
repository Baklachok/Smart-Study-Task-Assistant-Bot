import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AddTaskParseError(ValueError):
    """Ошибка парсинга команды /add_task"""


def parse_add_task(text: str) -> tuple[str, str | None, str | None]:
    """
    Парсит:
    /add_task Title | [YYYY-MM-DD HH:MM] | [low|medium|high]
    """

    try:
        _, task_str = text.split(" ", 1)
    except ValueError:
        logger.error("Неверный формат команды: %s", text)
        raise ValueError(
            "Неверный формат команды. Используйте: /add_task Title | [YYYY-MM-DD HH:MM] | [low|medium|high]"
        )

    parts = [p.strip() for p in task_str.split("|")]

    title = parts[0]
    due_at = None
    priority = None

    # Парсинг даты/приоритета из второго элемента
    if len(parts) >= 2 and parts[1]:
        try:
            due_at = datetime.strptime(parts[1], "%Y-%m-%d %H:%M").isoformat()
            logger.info("Парсинг даты успешен: %s", due_at)
        except ValueError:
            priority = parts[1].lower()
            logger.info("Второй параметр интерпретирован как приоритет: %s", priority)

    # Парсинг приоритета из третьего элемента
    if len(parts) >= 3 and parts[2]:
        priority = parts[2].lower()
        logger.info("Приоритет установлен: %s", priority)

    logger.info(
        "Задача распарсена: title='%s', due_at='%s', priority='%s'",
        title,
        due_at,
        priority,
    )
    return title, due_at, priority


def parse_add_course(text: str) -> tuple[str, str | None]:
    """
    /add_course Title | Description
    """
    _, data = text.split(" ", 1)
    parts = [p.strip() for p in data.split("|", 1)]

    title = parts[0]
    description = parts[1] if len(parts) > 1 else None

    logger.debug(
        "Parsed add_course command",
        extra={"title": title},
    )

    return title, description


def parse_add_topic(text: str) -> tuple[str, str]:
    """
    /add_topic Title | course_id
    """
    _, payload = text.split(" ", 1)
    parts = [p.strip() for p in payload.split("|")]

    if len(parts) != 2:
        raise ValueError("Invalid format")

    return parts[0], parts[1]
