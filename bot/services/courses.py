from typing import Any

from httpx import Response

from bot.config import settings
from bot.utils.http import api_client


async def fetch_courses(token: str) -> Any:
    """Возвращает список курсов с API"""
    async with api_client() as client:
        resp = await client.get(
            f"{settings.API_URL}/courses/", headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        return []
    return resp.json().get("results", [])


async def create_course(
    token: str,
    title: str,
    description: str | None,
) -> Response:
    """Создаёт курс через API и возвращает response"""
    payload = {"title": title}
    if description:
        payload["description"] = description

    async with api_client() as client:
        return await client.post(
            f"{settings.API_URL}/courses/",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
