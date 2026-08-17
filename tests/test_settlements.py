import pytest

pytest.importorskip("aiosqlite")

from sqlalchemy import select

from database.models import RoomSettlement

from services.debt_service import DebtService
from services.room_payment_service import (
    RoomPaymentService,
)
from services.settlement_service import (
    SettlementService,
)

from .helpers import create_users_and_room


async def test_create_settlement_is_pending(session):
    users, room, _ = await create_users_and_room(
        session
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=40.0,
    )

    await session.commit()

    assert settlement.status == "pending"
    assert settlement.amount == 40.0

    pending = (
        await SettlementService.get_pending_for_receiver(
            session=session,
            room_id=room.id,
            user_id=users[0].id,
        )
    )

    assert len(pending) == 1
    assert pending[0].id == settlement.id


async def test_only_receiver_can_confirm_settlement(session):
    users, room, _ = await create_users_and_room(
        session
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=40.0,
    )

    await session.commit()

    confirmed, status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=users[1].id,
        )
    )

    assert confirmed is None
    assert status == "not_receiver"

    confirmed, status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=users[0].id,
        )
    )

    await session.commit()

    assert status == "confirmed"
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at is not None


async def test_confirmed_settlement_reduces_debt(session):
    users, room, members = await create_users_and_room(
        session
    )

    await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        amount=100.0,
        description="Dinner",
    )

    await session.commit()

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    before = DebtService.calculate_details(
        members=members,
        payments=payments,
    )

    assert before["transfers"] == [
        {
            "from_user_id": users[1].id,
            "to_user_id": users[0].id,
            "amount": 50,
        }
    ]

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=50.0,
    )

    await session.commit()

    _, status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=users[0].id,
        )
    )

    await session.commit()

    confirmed = (
        await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room.id,
        )
    )

    after = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=confirmed,
    )

    assert status == "confirmed"
    assert after["balances"][users[0].id] == 0
    assert after["balances"][users[1].id] == 0
    assert after["transfers"] == []


async def test_cannot_confirm_same_settlement_twice(
    session,
):
    users, room, _ = await create_users_and_room(
        session
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=25.0,
    )

    await session.commit()

    first, first_status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=users[0].id,
        )
    )

    await session.commit()

    second, second_status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=users[0].id,
        )
    )

    assert first is not None
    assert first_status == "confirmed"

    assert second is None
    assert second_status == "already_confirmed"

    result = await session.execute(
        select(RoomSettlement).where(
            RoomSettlement.id == settlement.id
        )
    )

    stored = result.scalar_one()

    assert stored.status == "confirmed"