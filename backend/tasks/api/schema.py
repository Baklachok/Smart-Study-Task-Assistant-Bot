from drf_spectacular.utils import OpenApiParameter, OpenApiTypes


TASK_LIST_PARAMETERS = [
    OpenApiParameter(
        name="filter",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Фильтр задач: today или week.",
    ),
    OpenApiParameter(
        name="topic",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="UUID темы для фильтрации задач.",
    ),
]

HABITS_REPORT_PARAMETERS = [
    OpenApiParameter(
        name="days",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="Период отчета в днях. Допустимый диапазон: 7-90.",
    ),
]
