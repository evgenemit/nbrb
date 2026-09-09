from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, field_validator, model_validator


class TradeCreate(BaseModel):
    """Схема для создания обмена"""
    amount: Decimal
    from_cur_id: int
    to_cur_id: int

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Сумма должна быть больше 0')
        return v

    @model_validator(mode='after')
    def validate_cur_ids(self) -> Self:
        """Проверяет id валют на совпадение"""
        if self.from_cur_id == self.to_cur_id:
            raise ValueError('id валют должны быть разными')
        return self


class ReportParams(BaseModel):
    date_from: date
    date_to: date
    cur_id: int | None = None


class Report(BaseModel):
    cur_id: int
    sum_added: Decimal
    sum_removed: Decimal
    count: int
