import httpx
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client
