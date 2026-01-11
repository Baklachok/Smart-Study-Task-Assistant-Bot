from typing import Any

from bot.config import settings
from bot.utils.http import api_client


async def create_task(access_token: str, payload: dict[str, Any]) -> Any:
    async with api_client() as client:
        return await client.post(
            f"{settings.API_URL}/tasks/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )


async def fetch_tasks(access_token: str, filter_type: str | None) -> Any:
    async with api_client() as client:
        return await client.get(
            f"{settings.API_URL}/tasks/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"filter": filter_type} if filter_type else {},
        )
