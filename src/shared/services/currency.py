import logging
from decimal import Decimal

from shared.models.currency import Currency
from shared.repositories.currency import CurrencyRepository

logger = logging.getLogger(__name__)


class CurrencyService:
    def __init__(self, repo: CurrencyRepository) -> None:
        self._repo = repo

    async def upsert(self, currency: Currency) -> None:
        """Создать или обновить запись о валюте"""
        await self._repo.upsert(currency)

    async def add_byn(self) -> None:
        """Добавляет белорусский рубль"""
        logger.info('Добавление бел. рубля в хранилище')
        byn = Currency(
            abbreviation='BYN',
            name='Беллоруский рубль',
            scale=1,
            rate=Decimal(1)
        )
        exists = await self._repo.get_by(abbreviation=byn.abbreviation)
        if exists:
            return
        await self.upsert(byn)

    async def get_by(
        self, *,
        uid: int | None = None,
        abbreviation: str | None = None
    ) -> Currency | None:
        """Возвращает Currency по id"""
        if uid:
            return await self._repo.get_by(uid=uid)
        elif abbreviation:
            return await self._repo.get_by(abbreviation=abbreviation)


