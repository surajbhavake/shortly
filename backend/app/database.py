import redis.asyncio as redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.orm import DeclarativeBase
from .config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True

)

async def get_db():
    async with SessionLocal() as session:
        yield session