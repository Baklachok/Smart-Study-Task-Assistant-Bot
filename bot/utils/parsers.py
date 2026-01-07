import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AddTaskParseError(Exception):
    """Ошибка парсинга команды /add_task"""


def parse_add_task(text: str) -> tuple[str, str | None, str | None]:
    """
    Парсит:
    /add_task Title | [YYYY-MM-DD HH:MM] | [low|medium|high]
    """

    if " " not in text:
        logger.error("Неверный формат команды: %s", text)
        raise AddTaskParseError("Нет аргументов")

    _, payload = text.split(" ", 1)
    parts = [p.strip() for p in payload.split("|")]

    if not parts[0]:
        raise AddTaskParseError("Пустое название")

    title = parts[0]
    due_at = None
    priority = None

    if len(parts) >= 2 and parts[1]:
        try:
            due_at = datetime.strptime(parts[1], "%Y-%m-%d %H:%M").isoformat()
            logger.info("Парсинг даты успешен: %s", due_at)
        except ValueError:
            priority = parts[1].lower()
            logger.info("Второй параметр интерпретирован как приоритет: %s", priority)

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
