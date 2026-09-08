from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_session
from features.currency.repo import CurrencyRepository, CurrencySQLRepository
from features.currency.service import CurrencyService
from features.trade.repo import TradeRepository, TradeSQLRepository
from features.trade.service import TradeService


async def get_currency_repo(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> CurrencyRepository:
    """Возвращает объект для работы с курсами валют в хранилище"""
    return CurrencySQLRepository(session)


async def get_currency_service(
    repo: Annotated[CurrencyRepository, Depends(get_currency_repo)]
) -> CurrencyService:
    """Возвращает объект для работы с курсами валют"""
    return CurrencyService(repo)


async def get_trade_repo(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> TradeRepository:
    """Возвращает объект для работы с обменами в хранилище"""
    return TradeSQLRepository(session)


async def get_trade_service(
    repo: Annotated[TradeRepository, Depends(get_trade_repo)]
) -> TradeService:
    """Возвращает объект для работы с обменами"""
    return TradeService(repo)
