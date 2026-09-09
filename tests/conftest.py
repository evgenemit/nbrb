from datetime import date
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from api.dependencies import get_trade_repo, get_trade_service
from features.currency.models import Currency
from features.trade.models import TradeStatus, TradeUpdate
from features.trade.service import TradeService

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


@pytest_asyncio.fixture
async def test_currencies():
    c1 = Currency(
        id=10,
        name='Test 10',
        abbreviation='T10',
        scale=1,
        rate=Decimal(1)
    )
    c2 = Currency(
        id=11,
        name='Test 11',
        abbreviation='T11',
        scale=1,
        rate=Decimal('3.0665')
    )
    c3 = Currency(
        id=12,
        name='Test 12',
        abbreviation='T12',
        scale=1,
        rate=Decimal('3.5632')
    )
    c4 = Currency(
        id=13,
        name='Test 13',
        abbreviation='T13',
        scale=10,
        rate=Decimal('0.601')
    )
    c5 = Currency(
        id=14,
        name='Test 14',
        abbreviation='T14',
        scale=100000,
        rate=Decimal('0.2231')
    )
    return c1, c2, c3, c4, c5


@pytest_asyncio.fixture
async def trades_report(
    session: AsyncSession,
    test_currencies,
    trade_service: TradeService
):
    for c in test_currencies:
        session.add(c)
    await session.flush()
    c1, c2, c3, c4, c5 = test_currencies

    data = (
        (c1, c2, Decimal(120), TradeStatus.APPROVED, date(2026, 9, 1)),
        (c1, c3, Decimal('34.5'), TradeStatus.APPROVED, date(2026, 9, 3)),
        (c1, c4, Decimal('11.12'), TradeStatus.REJECTED, date(2026, 9, 5)),
        (c1, c5, Decimal(101), TradeStatus.APPROVED, date(2026, 9, 2)),
        (c2, c1, Decimal('12.98'), TradeStatus.APPROVED, date(2026, 9, 8)),
        (c2, c3, Decimal(100), TradeStatus.APPROVED, date(2026, 9, 4)),
        (c2, c4, Decimal(10), TradeStatus.APPROVED, date(2026, 9, 1)),
        (c2, c5, Decimal('13.76'), TradeStatus.APPROVED, date(2026, 9, 7)),
        (c3, c1, Decimal(200), TradeStatus.APPROVED, date(2026, 9, 3)),
        (c4, c2, Decimal('24.80'), TradeStatus.APPROVED, date(2026, 9, 2)),
        (c5, c3, Decimal('76.35'), TradeStatus.APPROVED, date(2026, 9, 2)),
        (c5, c2, Decimal(100), TradeStatus.APPROVED, date(2026, 9, 11)),
        (c4, c1, Decimal(67), TradeStatus.REJECTED, date(2026, 9, 2)),
    )

    full_data = []
    for d in data:
        t = await trade_service.create(d[0], d[1], d[2])
        t = await trade_service.update(TradeUpdate(id=t.id, status=d[3]))
        t.updated_at = d[4]
        session.add(t)
        full_data.append((t, d))
    await session.commit()
    yield full_data
    for c in test_currencies:
        await session.delete(c)
