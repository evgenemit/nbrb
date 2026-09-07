import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Self

from pydantic import BaseModel, field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel, func

from shared.models.currency import Currency, CurrencyPublic


class TradeStatus(str, Enum):
    APPROVED = 'approved'
    REJECTED = 'rejected'


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


class TradeBase(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)


class Trade(TradeBase, table=True):
    """Обмен валюты"""
    __tablename__ = 'trades'

    amount_original: Decimal
    amount: Decimal
    rate: Decimal = Field(max_digits=6, decimal_places=4)
    updated_at: datetime = Field(
        sa_column_kwargs={
            'server_default': func.now(),
            'onupdate': func.now(),
        }
    )
    status: TradeStatus | None = None
    from_cur_id: int = Field(foreign_key='currencies.id')
    to_cur_id: int = Field(foreign_key='currencies.id')
    from_cur: Currency = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Trade.from_cur_id]'}
    )
    to_cur: Currency = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Trade.to_cur_id]'}
    )


class TradePublic(TradeBase):
    amount: float
    rate: float

    model_config = {
        'json_schema_extra': {
            'examples': [{
                'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                'amount': 35.4,
                'rate': 1.1601,
            }]
        }
    }


class TradePublicFull(TradePublic):
    from_cur: CurrencyPublic
    to_cur: CurrencyPublic


class TradeUpdate(TradeBase):
    status: TradeStatus
