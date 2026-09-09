from datetime import date
from decimal import ROUND_DOWN, Decimal
from uuid import UUID

import pytest
import pytest_asyncio
from conftest import CUR1, CUR2
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete, select

from api.main import app
from core.database import get_session
from features.currency.models import CurrencyPublic
from features.trade.models import Trade, TradePublic, TradeStatus
from features.trade.schemas import Report, ReportParams, TradeCreate


@pytest_asyncio.fixture
async def client(async_session):

    async def override_get_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_currencies(client):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.get('/currencies/')
    CUR1_PUB = CurrencyPublic(
        abbreviation=CUR1.abbreviation,
        name=CUR1.name,
        scale=CUR1.scale,
        id=CUR1.id,
        rate=CUR1.rate
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    curpub_keys = CUR1_PUB.model_dump().keys()
    assert all(
        curpub_keys == c.keys()
        for c in data
    )
    assert data[0]['id'] == CUR1.id
    assert data[0]['full_name'] == f'{CUR1.scale} {CUR1.name}'
    assert Decimal(str(data[0]['rate'])) == CUR1.rate
    assert data[1]['id'] == CUR2.id
    assert data[1]['full_name'] == f'{CUR2.scale} {CUR2.name}'
    assert Decimal(str(data[1]['rate'])) == CUR2.rate


@pytest.mark.asyncio
async def test_create_trade_success(
    client,
    session
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=1,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    assert response.status_code == 200
    trade_public = TradePublic.model_validate(response.json())
    trade: Trade = (await session.exec(
        select(Trade).where(Trade.id == trade_public.id)
    )).one()
    assert trade.from_cur_id == test_data.from_cur_id
    assert trade.to_cur_id == test_data.to_cur_id
    assert trade.amount_original == test_data.amount
    test_rate = (CUR1.rate / CUR1.scale) * (CUR2.scale / CUR2.rate)
    test_rate = test_rate.quantize(Decimal('0.0000'), rounding=ROUND_DOWN)
    test_amount = test_data.amount * test_rate
    test_amount = test_amount.quantize(Decimal('0.00'), rounding=ROUND_DOWN)
    assert test_rate == trade.rate
    assert test_amount == trade.amount
    assert trade.status is None
    await session.delete(trade)
    await session.commit()


@pytest.mark.asyncio
async def test_create_trade_404(
    client
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=3,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_trade_val(
    client
):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json={
            'amount': 0, 'from_cur_id': 1, 'to_cur_id': 2
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_trade_status(
    client,
    session
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=1,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    uid = UUID(response.json().get('id'))
    trade = await session.get(Trade, uid)
    assert trade.status is None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.patch(
            '/trades/',
            json={'id': str(uid), 'status': TradeStatus.APPROVED}
        )
    assert response.status_code == 200
    await session.refresh(trade)
    assert trade.status == TradeStatus.APPROVED
    await session.delete(trade)
    await session.commit()


@pytest.mark.asyncio
async def test_update_trade_status_already_exists(
    client,
    session
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=1,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    uid = UUID(response.json().get('id'))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.patch(
            '/trades/',
            json={'id': str(uid), 'status': TradeStatus.APPROVED}
        )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.patch(
            '/trades/',
            json={'id': str(uid), 'status': TradeStatus.REJECTED}
        )
    assert response.status_code == 409
    trade = await session.get(Trade, uid)
    assert trade.status == TradeStatus.APPROVED
    await session.delete(trade)
    await session.commit()


@pytest.mark.asyncio
async def test_update_trade_status_not_exists(
    client,
):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.patch(
            '/trades/',
            json={'id': '018f4a3c-b26a-7123-8abc-def012345678', 'status': TradeStatus.APPROVED}
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_uncomplete_trades(
    client,
    session
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=1,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    uid = response.json().get('id')

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.get('/trades/uncomplete/')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['id'] == uid
    await session.exec(delete(Trade).where(Trade.id == UUID(uid)))
    await session.commit()


@pytest.mark.asyncio
async def test_get_uncomplete_trades_approved(
    client,
    session
):
    test_data = TradeCreate(
        amount=Decimal(120),
        from_cur_id=1,
        to_cur_id=2
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.post('/trades/', json=test_data.model_dump(mode='json'))
    uid = UUID(response.json().get('id'))
    trade = await session.get(Trade, uid)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.get('/trades/uncomplete/')
    assert len(response.json()) == 1

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.patch(
            '/trades/',
            json={'id': str(uid), 'status': TradeStatus.APPROVED}
        )
    assert response.status_code == 200

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.get('/trades/uncomplete/')
    assert len(response.json()) == 0

    await session.delete(trade)
    await session.commit()


def create_report(data: dict, report_params: ReportParams):
    report = {}
    for t, d in data:
        if d[3] != TradeStatus.APPROVED:
            continue
        if report_params.date_from > d[4]:
            continue
        if report_params.date_to < d[4]:
            continue
        report_data = report.get(
            d[0].id,
            {'added': Decimal(0), 'removed': Decimal(0), 'count': 0}
        )
        report_data['count'] += 1
        report_data['added'] += t.amount_original
        report[d[0].id] = report_data

        report_data = report.get(
            d[1].id,
            {'added': Decimal(0), 'removed': Decimal(0), 'count': 0}
        )
        report_data['count'] += 1
        report_data['removed'] += t.amount
        report[d[1].id] = report_data
    res = []
    for cur_id, value in report.items():
        if report_params.cur_id and cur_id != report_params.cur_id:
            continue
        res.append(Report(
            cur_id=cur_id,
            sum_added=value['added'].quantize(Decimal('0.00'), rounding=ROUND_DOWN),
            sum_removed=value['removed'].quantize(Decimal('0.00'), rounding=ROUND_DOWN),
            count=value['count']
        ).model_dump(mode='json'))
    res = sorted(res, key=lambda x: x['cur_id'])
    return res


@pytest.mark.asyncio
@pytest.mark.parametrize("date_from, date_to, cur_id", [
    (date(2026, 9, 2), date(2026, 9, 7), None),
    (date(2026, 9, 1), date(2026, 9, 7), 11),
    (date(2026, 9, 4), date(2026, 9, 4), None),
    (date(2026, 8, 2), date(2026, 10, 1), None),
])
async def test_get_report(
    date_from, date_to, cur_id,
    client,
    trades_report,
    session,
    test_currencies
):
    report_params = ReportParams(
        date_from=date_from,
        date_to=date_to,
        cur_id=cur_id
    )
    params = {
        k: v for k, v in
        report_params.model_dump(mode='json').items()
        if v
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        response = await ac.get('/trades/', params=params)
    assert response.status_code == 200

    expected_report = create_report(trades_report, report_params)
    assert response.json() == expected_report

    for tr in trades_report:
        await session.delete(tr[0])
    for c in test_currencies:
        await session.delete(c)
    await session.commit()
