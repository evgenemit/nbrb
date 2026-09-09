from decimal import ROUND_DOWN, Decimal

from fastapi import HTTPException, status

from features.currency.models import Currency
from features.trade.exceptions import TradeStatusAlreadySet
from features.trade.models import Trade, TradeUpdate
from features.trade.repo import TradeRepository
from features.trade.schemas import Report, ReportParams


class TradeService:
    def __init__(self, repo: TradeRepository) -> None:
        self._repo = repo

    def _calculate_rate(
        self,
        from_cur: Currency,
        to_cur: Currency
    ) -> Decimal:
        """Рассчитать курс между двумя валютами"""
        rate = (from_cur.rate / from_cur.scale) * (to_cur.scale / to_cur.rate)
        return rate.quantize(Decimal('0.0000'), rounding=ROUND_DOWN)

    def _calculate_amount(
        self,
        amount: Decimal,
        rate: Decimal
    ) -> Decimal:
        """Рассчитать итоговую сумму по курсу"""
        return (amount * rate).quantize(Decimal('0.00'), rounding=ROUND_DOWN)

    async def create(
        self,
        from_cur: Currency,
        to_cur: Currency,
        amount: Decimal
    ) -> Trade:
        """Создать запись обмена валют"""
        trade_rate = self._calculate_rate(from_cur, to_cur)
        trade_amount = self._calculate_amount(amount, trade_rate)

        trade = Trade(
            amount_original=amount,
            amount=trade_amount,
            rate=trade_rate,
            from_cur_id=from_cur.id,
            to_cur_id=to_cur.id
        )
        return await self._repo.create(trade)

    async def uncomplete(self) -> list[Trade]:
        """Возвращает список незавершенных сделок"""
        return await self._repo.get_by_status(status=None)

    async def update(self, update_data: TradeUpdate) -> Trade:
        """Обновляет статус сделки"""
        try:
            trade = await self._repo.update_status(
                update_data.id,
                update_data.status
            )
            if trade is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            return trade
        except TradeStatusAlreadySet as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{e}'
            )

    async def report(self, report_params: ReportParams) -> list[Report]:
        return await self._repo.report(
            report_params.date_from,
            report_params.date_to,
            report_params.cur_id
        )
