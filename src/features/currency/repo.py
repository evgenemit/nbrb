import logging
from typing import Protocol

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from features.currency.models import Currency

logger = logging.getLogger(__name__)


class CurrencyRepository(Protocol):
    async def upsert(self, currency: Currency) -> None: ...
    async def get_all(self) -> list[Currency]: ...
    async def get_by(
        self, *, uid: int | None = None, abbreviation: str | None = None
    ) -> Currency | None: ...


class CurrencySQLRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, currency: Currency) -> None:
        """Создать или обновить запись о валюте в хранилище"""
        if not isinstance(currency, Currency):
            return
        if currency.id is not None:
            data = await self._session.get(Currency, currency.id)
            if data and data.rate != currency.rate:
                data.rate = currency.rate
                currency = data
            elif data and data.rate == currency.rate:
                logger.info(f'Курс валюты {data.abbreviation} не изменился')
                return
        logger.info(
            f'Сохранение курса валюты {currency.abbreviation} '
            f'{currency.rate}'
        )
        self._session.add(currency)
        await self._session.flush()

    async def get_all(self) -> list[Currency]:
        """Получить все курсы валют из храналища"""
        logger.info('Запрос всех курсов валют из хранилища')
        stmt = select(Currency).order_by(Currency.name)
        return (await self._session.exec(stmt)).all()

    async def get_by(
        self, *,
        uid: int | None = None,
        abbreviation: str | None = None,
    ) -> Currency | None:
        """Возвращает Currency по id/abbreviation из хранилища"""
        if uid and isinstance(uid, int):
            return await self._session.get(Currency, uid)
        elif abbreviation and isinstance(abbreviation, str):
            stmt = select(Currency).where(Currency.abbreviation == abbreviation)
            return (await self._session.exec(stmt)).one_or_none()
