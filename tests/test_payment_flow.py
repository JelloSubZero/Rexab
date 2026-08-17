import pytest

pytest.importorskip("aiosqlite")

from services.debt_service import DebtService
from services.room_payment_service import RoomPaymentService

from .helpers import create_users_and_room


async def test_delete_payment_recalculates_debt(session):
    users, room, members = await create_users_and_room(
        session,
        count=2,
    )

    payer = users[0]
    debtor = users[1]

    payment = await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=payer.id,
        amount=100.0,
        description="Dinner",
    )

    await session.commit()

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    details_before = DebtService.calculate_details(
        members=members,
        payments=payments,
    )

    assert details_before["balances"][payer.id] == 50
    assert details_before["balances"][debtor.id] == -50

    deleted = await RoomPaymentService.delete_payment(
        session=session,
        payment_id=payment.id,
    )

    await session.commit()

    assert deleted is True

    payments_after = (
        await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room.id,
        )
    )

    assert payments_after == []

    details_after = DebtService.calculate_details(
        members=members,
        payments=payments_after,
    )

    assert details_after["balances"][payer.id] == 0
    assert details_after["balances"][debtor.id] == 0
    assert details_after["transfers"] == []