from typing import Any

FIELD_NAMES = {
    "title": "Название",
    "description": "Описание",
    "due_at": "Дедлайн",
    "priority": "Приоритет",
}


def format_api_errors(error_json: Any) -> str:
    messages: list[str] = []

    for field, errors in error_json.items():
        field_name = FIELD_NAMES.get(field, field)

        if isinstance(errors, list):
            for error in errors:
                messages.append(f"• {field_name}: {error}")
        else:
            messages.append(f"• {field_name}: {errors}")

    return "\n".join(messages)
