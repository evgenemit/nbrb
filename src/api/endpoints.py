from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_currency_service, get_trade_service
from features.currency.models import CurrencyPublic
from features.currency.service import CurrencyService
from features.trade.models import TradePublic, TradePublicFull, TradeUpdate
from features.trade.schemas import Report, ReportParams, TradeCreate
from features.trade.service import TradeService

router = APIRouter()


@router.get('/currencies/')
async def get_currencies(
    currency_service: Annotated[CurrencyService, Depends(get_currency_service)],
) -> list[CurrencyPublic]:
    """Получить все доступные для обмена валюты"""
    return await currency_service.get_all()


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
    return await trade_service.create(from_cur, to_cur, trade_create.amount)


@router.patch('/trades/')
async def update_trade_status(
    trade_update: TradeUpdate,
    trade_service: Annotated[TradeService, Depends(get_trade_service)],
) -> TradeUpdate:
    """Второй этап обмена валют. Подтверждение/отклонение сделки"""
    return await trade_service.update(trade_update)


@router.get('/trades/uncomplete/')
async def get_unapproved_trades(
    trade_service: Annotated[TradeService, Depends(get_trade_service)]
) -> list[TradePublicFull]:
    """Получить список незавершенных сделок"""
    return await trade_service.uncomplete()


@router.get('/trades/')
async def get_report(
    report_params: Annotated[ReportParams, Query()],
    trade_service: Annotated[TradeService, Depends(get_trade_service)]
) -> list[Report]:
    """Информация о сделках за интервал времени"""
    return await trade_service.report(report_params)
