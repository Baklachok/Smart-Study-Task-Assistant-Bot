from datetime import datetime


def parse_add_task(text: str) -> tuple[str, str | None, str | None]:
    """
    Парсит:
    /add_task Title | [YYYY-MM-DD HH:MM] | [low|medium|high]
    """

    _, task_str = text.split(" ", 1)
    parts = [p.strip() for p in task_str.split("|")]

    title = parts[0]
    due_at = None
    priority = None

    if len(parts) >= 2 and parts[1]:
        try:
            due_at = datetime.strptime(parts[1], "%Y-%m-%d %H:%M").isoformat()
        except ValueError:
            priority = parts[1].lower()

    if len(parts) >= 3 and parts[2]:
        priority = parts[2].lower()

    return title, due_at, priority
