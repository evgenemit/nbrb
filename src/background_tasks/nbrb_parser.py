import logging
from json.decoder import JSONDecodeError

import httpx

from api.dependencies import get_currency_repo, get_currency_service
from core.config import settings
from core.database import session_maker
from features.currency.models import Currency
from features.currency.service import CurrencyService

logger = logging.getLogger(__name__)


async def fetch_currencies(periodicity: int) -> list[Currency] | None:
    """Получить курсы валют"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            settings.API_URL,
            params={'periodicity': periodicity}
        )
        if resp.status_code != httpx.codes.OK:
            logger.error(f'Ошибка выполнения запроса к API {resp.status_code}')
            return
        try:
            data = resp.json()
        except JSONDecodeError:
            return
    return [Currency.model_validate(cur_data) for cur_data in data]


async def save_curriency(
    currency: Currency,
    service: CurrencyService
) -> None:
    """Сохранить полученные данные о курсе валюты"""
    await service.upsert(currency)


async def update_currencies(
    periodicity: int,
    session_maker = session_maker
) -> None:
    """Получить и обновить данные о курсах валют"""
    logger.info(f'Запуск задачи ({periodicity=})')
    currencies = await fetch_currencies(periodicity)
    if currencies is None:
        logger.info(f'Задача завершена c ошибкой ({periodicity=})')
        return
    async with session_maker() as session:
        repo = await get_currency_repo(session)
        service = await get_currency_service(repo)
        for currency in currencies:
            await save_curriency(currency, service)
    logger.info(f'Задача завершена ({periodicity=})')


async def add_byn(session_maker = session_maker) -> None:
    """Добавить белорусский рубль в хранилище"""
    async with session_maker() as session:
        repo = await get_currency_repo(session)
        service = await get_currency_service(repo)
        await service.add_byn()
