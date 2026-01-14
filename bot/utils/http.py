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
    task_id: str | None, method: str, token: str, data: dict[str, Any] | None = None
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


def auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def post_entity(
    endpoint: str,
    token: str | None,
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Универсальный POST-запрос"""
    async with api_client() as client:
        response = await client.post(
            f"{settings.API_URL}/{endpoint}/", headers=auth_headers(token), json=payload
        )
        return (
            response.status_code,
            response.json() if response.status_code != 204 else {},
        )


async def get_entities(
    endpoint: str, token: str, params: dict[str, Any] | None = None
) -> tuple[int, list[dict[str, Any]]]:
    """Универсальный GET-запрос"""
    async with api_client() as client:
        response = await client.get(
            f"{settings.API_URL}/{endpoint}/",
            headers=auth_headers(token),
            params=params,
        )
        return response.status_code, response.json().get(
            "results", []
        ) if response.status_code == 200 else []
