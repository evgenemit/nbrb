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
