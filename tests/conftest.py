from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from nbrb.dependencies import get_trade_repo, get_trade_service
from shared.models.currency import Currency

CUR1 = Currency(
    id=1,
    name='Test 1',
    abbreviation='TS1',
    scale=10,
    rate=Decimal('3.42')
)
CUR2 = Currency(
    id=2,
    name='Test 2',
    abbreviation='TS2',
    scale=100,
    rate=Decimal('1.15')
)


@pytest_asyncio.fixture(scope='session')
async def engine():
    return create_async_engine('sqlite+aiosqlite:///:memory:')


@pytest_asyncio.fixture(scope='session')
async def async_session(engine):
    return async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest_asyncio.fixture
async def session(async_session):
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope='session', autouse=True)
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        yield
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope='session', autouse=True)
async def fill_database(async_session, create_tables):
    async with async_session() as session:
        session.add(CUR1)
        session.add(CUR2)
        await session.commit()


@pytest_asyncio.fixture
async def trade_service(session):
    repo = await get_trade_repo(session)
    yield await get_trade_service(repo)
