from typing import Any


def format_topic(topic: dict[str, Any]) -> str:
    return (
        f"📘 <b>{topic['title']}</b>\n"
        f"📚 Курс: {topic.get('course_name', 'Без курса')}\n"
        f"✅ Прогресс: {topic.get('progress', 0)}%"
    )
