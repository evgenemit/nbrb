import uuid
from datetime import date
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, func

from features.currency.models import Currency, CurrencyPublic


class TradeStatus(str, Enum):
    APPROVED = 'approved'
    REJECTED = 'rejected'


class TradeBase(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)


class Trade(TradeBase, table=True):
    """Обмен валюты"""
    __tablename__ = 'trades'

    amount_original: Decimal = Field(decimal_places=2)
    amount: Decimal = Field(decimal_places=2)
    rate: Decimal = Field(max_digits=12, decimal_places=4)
    updated_at: date = Field(
        sa_column_kwargs={
            'server_default': func.current_date(),
            'onupdate': func.current_date(),
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
