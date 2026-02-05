from __future__ import annotations

from dataclasses import dataclass


DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


@dataclass(frozen=True)
class HabitsReport:
    short_text: str
    long_text: str
    metrics: dict[str, object]
