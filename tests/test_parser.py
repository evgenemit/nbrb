import pytest
from httpx import Response

from background_tasks.nbrb_parser import fetch_currencies
from features.currency.models import Currency


@pytest.mark.asyncio
async def test_fetch_curriences_ok(respx_mock):
    respx_mock.get('https://api.nbrb.by/exrates/rates').mock(
        return_value=Response(
            200,
            json=[
                {
                    "Cur_ID": 440,
                    "Date": "2026-09-07T00:00:00",
                    "Cur_Abbreviation": "AUD",
                    "Cur_Scale": 1,
                    "Cur_Name": "Австралийский доллар",
                    "Cur_OfficialRate": 2.2142
                },
                {
                    "Cur_ID": 510,
                    "Date": "2026-09-07T00:00:00",
                    "Cur_Abbreviation": "AMD",
                    "Cur_Scale": 1000,
                    "Cur_Name": "Армянских драмов",
                    "Cur_OfficialRate": 9.1131
                }
            ]
        )
    )

    currencies = await fetch_currencies(0)
    assert len(currencies) == 2
    assert all(isinstance(c, Currency) for c in currencies)
    assert currencies[0].id == 440
    assert currencies[1].id == 510


@pytest.mark.asyncio
async def test_fetch_curriences_satus_not_200(respx_mock):
    respx_mock.get('https://api.nbrb.by/exrates/rates').mock(
        return_value=Response(400)
    )
    data = await fetch_currencies(0)
    assert data is None


@pytest.mark.asyncio
async def test_fetch_curriences_not_json(respx_mock):
    respx_mock.get('https://api.nbrb.by/exrates/rates').mock(
        return_value=Response(200)
    )
    data = await fetch_currencies(0)
    assert data is None
