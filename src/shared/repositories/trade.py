from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.exceptions import TradeStatusAlreadySet
from shared.models.trade import Trade, TradeStatus


class TradeRepository(Protocol):
    async def create(self, trade: Trade) -> Trade: ...
    async def get_by_status(self, status: TradeStatus | None) -> list[Trade]: ...
    async def update_status(self, trade_id: UUID, status: TradeStatus) -> Trade | None: ...


class TradeSQLRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, trade: Trade) -> Trade:
        """Создать запись обмена валют в хранилище"""
        self._session.add(trade)
        await self._session.commit()
        await self._session.refresh(trade)
        return trade

    async def get_by_status(self, status: TradeStatus | None) -> list[Trade]:
        """Список сделок по статусу из храналища"""
        stmt = select(Trade).where(Trade.status == status).options(
            selectinload(Trade.from_cur),
            selectinload(Trade.to_cur)
        )
        trades = (await self._session.exec(stmt)).all()
        return trades

    async def update_status(self, trade_id: UUID, status: TradeStatus) -> Trade | None:
        """Обновить статус сделки в хранилище"""
        stmt = select(Trade).where(Trade.id == trade_id)
        trade = (await self._session.exec(stmt)).one_or_none()
        if trade:
            if trade.status is not None:
                raise TradeStatusAlreadySet(trade.status)
            trade.status = status
            self._session.add(trade)
            await self._session.commit()
            await self._session.refresh(trade)
        return trade
