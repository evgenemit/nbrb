from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from redis_fastapi import CacheBackend
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings

engine = create_async_engine(settings.DB_URL)
session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session():
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


@asynccontextmanager
async def get_redis_cache(eviction_group: str) -> AsyncGenerator[CacheBackend]:
    async with Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    ) as r:
        cache = CacheBackend(r, eviction_group=eviction_group)
        yield cache

