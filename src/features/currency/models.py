from decimal import Decimal

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class CurrencyBase(SQLModel):
    abbreviation: str = Field(validation_alias='Cur_Abbreviation')
    name: str = Field(validation_alias='Cur_Name')
    scale: int = Field(validation_alias='Cur_Scale')


class Currency(CurrencyBase, table=True):
    """Валюта"""
    __tablename__ = 'currencies'

    id: int | None = Field(
        default=None, primary_key=True, validation_alias='Cur_ID'
    )
    rate: Decimal = Field(
        max_digits=12, decimal_places=4, validation_alias='Cur_OfficialRate'
    )

    model_config = {
        'populate_by_name': True
    }


class CurrencyPublic(CurrencyBase):
    id: int
    rate: float
    name: str = Field(exclude=True)
    scale: int = Field(exclude=True)

    model_config = {
        'populate_by_name': True
    }

    @computed_field
    @property
    def full_name(self) -> str:
        return f'{self.scale} {self.name}'
