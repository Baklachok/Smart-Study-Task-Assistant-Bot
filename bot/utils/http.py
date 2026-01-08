import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from bot.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client


async def task_api_request(
    task_id: str, method: str, token: str, data: dict[str, Any] | None = None
) -> httpx.Response:
    """
    Универсальный API-запрос для задачи.
    method: 'patch' или 'delete'
    """
    headers = {"Authorization": f"Bearer {token}"}
    logger.info("API request: method=%s task_id=%s data=%s", method, task_id, data)

    async with api_client() as client:
        if method == "patch":
            response = await client.patch(
                f"{settings.API_URL}/tasks/{task_id}/", headers=headers, json=data
            )
        elif method == "delete":
            response = await client.delete(
                f"{settings.API_URL}/tasks/{task_id}/", headers=headers
            )
        else:
            logger.error("Unsupported HTTP method: %s", method)
            raise ValueError(f"Unsupported method: {method}")

    logger.info(
        "API response: task_id=%s status=%s response_text=%s",
        task_id,
        response.status_code,
        response.text,
    )
    return response
