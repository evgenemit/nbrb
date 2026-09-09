from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from features.trade.exceptions import TradeStatusAlreadySet
from features.trade.models import Trade, TradeStatus
from features.trade.schemas import Report


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
        await self._session.flush()
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
            await self._session.flush()
            await self._session.refresh(trade)
        return trade

    async def report(
        self,
        from_date: date,
        to_date: date,
        cur_id: int | None = None
    ) -> list[Report]:
        conditions = [
            Trade.updated_at >= from_date,
            Trade.updated_at <= to_date,
            Trade.status == TradeStatus.APPROVED
        ]
        conditions_added = conditions.copy()
        conditions_removed = conditions.copy()
        if cur_id:
            conditions_added.append(Trade.from_cur_id == cur_id)
            conditions_removed.append(Trade.to_cur_id == cur_id)

        added_stmt = select(
            Trade.from_cur_id,
            func.sum(Trade.amount_original).label('sum_a'),
            func.count(Trade.id).label('count_a')
        ).where(
            *conditions_added,
        ).group_by(Trade.from_cur_id).cte('added')
        removed_stmt = select(
            Trade.to_cur_id,
            func.sum(Trade.amount).label('sum_r'),
            func.count(Trade.id).label('count_r')
        ).where(
            *conditions_removed,
        ).group_by(Trade.to_cur_id).cte('removed')

        stmt = select(
            func.coalesce(added_stmt.c.from_cur_id, removed_stmt.c.to_cur_id).label('cur_id'),
            func.coalesce(added_stmt.c.sum_a, 0).label('sum_added'),
            func.coalesce(removed_stmt.c.sum_r, 0).label('sum_removed'),
            added_stmt.c.count_a, removed_stmt.c.count_r,
            (func.coalesce(added_stmt.c.count_a, 0) + func.coalesce(removed_stmt.c.count_r, 0)).label('count')
        ).join(removed_stmt, added_stmt.c.from_cur_id == removed_stmt.c.to_cur_id, full=True).order_by('cur_id')

        data = (await self._session.exec(stmt)).all()
        report = [Report.model_validate(r._mapping) for r in data]
        return report
