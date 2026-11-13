import pytest_asyncio
import httpx
from asgi_lifespan import LifespanManager
from sqlalchemy import text

from app.database import engine, redis_client
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c
        # Cleanup between tests — runs BEFORE lifespan shutdown
        await redis_client.flushdb()
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE links"))