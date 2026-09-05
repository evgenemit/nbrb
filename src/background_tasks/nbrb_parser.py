import logging

import httpx

from shared.database import session_maker
from shared.models import Currency
from shared.repositories import CurrencyRepository, CurrencySQLRepository

logger = logging.getLogger(__name__)


async def fetch_currencies(periodicity: int) -> list[Currency]:
    """Получить курсы валют"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            'https://api.nbrb.by/exrates/rates',
            params={'periodicity': periodicity}
        )
        if resp.status_code != httpx.codes.OK:
            logger.error(f'Ошибка выполнения запроса к API {resp.status_code}')
            return
        data = resp.json()
    return [Currency.from_dict(cur_data) for cur_data in data]


async def save_curriency(
    currency: Currency,
    repo: CurrencyRepository
) -> None:
    """Сохранить полученные данные о курсе валюты"""
    await repo.upsert(currency)


async def update_currencies(periodicity: int):
    """Получить и обновить данные о курсах валют"""
    logger.info(f'Запуск задачи ({periodicity=})')
    currencies = await fetch_currencies(periodicity)
    async with session_maker() as session:
        repo = CurrencySQLRepository(session)
        for currency in currencies:
            await save_curriency(currency, repo)
    logger.info(f'Задача завершена ({periodicity=})')
