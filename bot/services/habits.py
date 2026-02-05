import httpx

from bot.config import settings
from bot.utils.http import api_client


async def fetch_habits_report(
    access_token: str, days: int | None = None
) -> httpx.Response:
    params: dict[str, int] = {}
    if days:
        params["days"] = days

    async with api_client() as client:
        return await client.get(
            f"{settings.API_URL}/tasks/habits/",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=httpx.Timeout(10.0),
        )
