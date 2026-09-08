from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_currency_repo, get_currency_service, get_trade_service
from features.currency.models import CurrencyPublic
from features.currency.repo import CurrencyRepository
from features.currency.service import CurrencyService
from features.trade.models import TradeCreate, TradePublic, TradePublicFull, TradeUpdate
from features.trade.service import TradeService

router = APIRouter()


@router.get('/currencies/')
async def get_currencies(
    currency_repo: Annotated[CurrencyRepository, Depends(get_currency_repo)],
) -> list[CurrencyPublic]:
    """Получить все доступные для обмена валюты"""
    currencies = await currency_repo.get_all()
    return currencies


@router.post('/trades/')
async def create_trade(
    trade_create: TradeCreate,
    trade_service: Annotated[TradeService, Depends(get_trade_service)],
    cur_service: Annotated[CurrencyService, Depends(get_currency_service)],
) -> TradePublic:
    """Первый этап обмена валют. Создание сделки"""
    from_cur = await cur_service.get_by(uid=trade_create.from_cur_id)
    if from_cur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    to_cur = await cur_service.get_by(uid=trade_create.to_cur_id)
    if to_cur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    trade = await trade_service.create(from_cur, to_cur, trade_create.amount)
    return trade


@router.patch('/trades/')
async def update_trade_status(
    trade_update: TradeUpdate,
    trade_service: Annotated[TradeService, Depends(get_trade_service)],
) -> TradeUpdate:
    """Второй этап обмена валют. Подтверждение/отклонение сделки"""
    return await trade_service.update(trade_update)


@router.get('/trades/unapproved/')
async def get_unapproved_trades(
    trade_service: Annotated[TradeService, Depends(get_trade_service)]
) -> list[TradePublicFull]:
    """Получить список незавершенных сделок"""
    return await trade_service.unapproved()
