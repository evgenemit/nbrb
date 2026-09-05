from decimal import Decimal

from sqlmodel import Field, SQLModel


class Currency(SQLModel, table=True):
    """Валюта"""
    __tablename__ = 'currencies'

    id: int | None = Field(default=None, primary_key=True)
    abbreviation: str
    name: str
    scale: int
    officialrate: Decimal = Field(max_digits=6, decimal_places=4)

    @classmethod
    def from_dict(cls, data: dict) -> Currency:
        new_data = {
            key.replace('Cur_', '').lower(): value 
            for key, value in data.items()
        }
        return cls.model_validate(new_data)
