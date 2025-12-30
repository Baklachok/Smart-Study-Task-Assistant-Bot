import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
