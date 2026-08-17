import pytest

pytest.importorskip("aiosqlite")

from sqlalchemy import select

from database.models import RoomPayment
from services.debt_service import DebtService
from services.room_payment_service import (
    RoomPaymentService,
)

from .helpers import create_users_and_room


async def test_create_payment_and_calculate_debt(session):
    users, room, members = await create_users_and_room(
        session
    )

    payment = await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        amount=120.0,
        description="Dinner",
    )

    await session.commit()

    assert payment.id is not None

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    assert len(payments) == 1
    assert payments[0].amount == 120.0
    assert payments[0].description == "Dinner"

    details = DebtService.calculate_details(
        members=members,
        payments=payments,
    )

    assert details["total"] == 120
    assert details["share"] == 60
    assert details["balances"][users[0].id] == 60
    assert details["balances"][users[1].id] == -60


async def test_delete_payment_removes_it(session):
    users, room, _ = await create_users_and_room(
        session
    )

    payment = await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        amount=75.0,
        description="Coffee",
    )

    await session.commit()

    deleted = await RoomPaymentService.delete_payment(
        session=session,
        payment_id=payment.id,
    )

    await session.commit()

    assert deleted is True

    remaining = await session.execute(
        select(RoomPayment).where(
            RoomPayment.id == payment.id
        )
    )

    assert remaining.scalar_one_or_none() is None


async def test_delete_missing_payment_returns_false(session):
    result = await RoomPaymentService.delete_payment(
        session=session,
        payment_id=999999,
    )

    assert result is False