from typing import Any

from bot.config import settings
from bot.utils.http import api_client


async def fetch_topics(access_token: str, course_id: str | None = None) -> Any:
    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/topics/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"course": course_id},
        )
    if response.status_code != 200:
        return []
    return response.json().get("results", [])
