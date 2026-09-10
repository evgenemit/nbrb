import logging
from decimal import Decimal

from core.database import get_redis_cache
from features.currency.models import Currency
from features.currency.repo import CurrencyRepository

logger = logging.getLogger(__name__)


class CurrencyService:
    def __init__(self, repo: CurrencyRepository) -> None:
        self._repo = repo

    async def upsert(self, currency: Currency) -> None:
        """Создать или обновить запись о валюте"""
        await self._repo.upsert(currency)

    async def add_byn(self) -> None:
        """Добавить белорусский рубль"""
        logger.info('Добавление бел. рубля')
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
        """Возвращает Currency по id/abbreviation"""
        if not (uid or abbreviation):
            return
        async with get_redis_cache(eviction_group='currencies') as cache:
            if uid:
                cached = await cache.get(
                    f'currency:{uid}', eviction_group='currencies'
                )
                if cached is not None:
                    return Currency.model_validate(cached)
            result = await self._repo.get_by(
                uid=uid, abbreviation=abbreviation
            )
            if uid and result:
                await cache.set(
                    f'currency:{uid}',
                    result.model_dump(mode='json'),
                    eviction_group='currencies'
                )
            return result

    async def get_all(self) -> list[Currency]:
        """Получить все курсы валют"""
        return await self._repo.get_all()
