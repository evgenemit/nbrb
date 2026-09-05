import logging
from typing import Protocol

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.models import Currency

logger = logging.getLogger(__name__)


class CurrencyRepository(Protocol):
    async def upsert(self, currency: Currency) -> None: ...


class CurrencySQLRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, currency: Currency) -> None:
        """Создать или обновить запись о валюте"""
        stmt = select(Currency).where(Currency.id == currency.id)
        data = (await self._session.exec(stmt)).one_or_none()
        if data and data.officialrate != currency.officialrate:
            logger.info(
                f'Курс валюты {data.abbreviation}'
                f'{data.officialrate} -> {currency.officialrate}'
            )
            data.officialrate = currency.officialrate
            currency = data
        elif data and data.officialrate == currency.officialrate:
            logger.info(f'Курс валюты {data.abbreviation} не изменился')
            return
        self._session.add(currency)
        await self._session.commit()
