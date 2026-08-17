import pytest

pytest.importorskip("aiosqlite")

from services.debt_service import DebtService
from services.receipt_service import ReceiptService
from services.room_payment_service import RoomPaymentService
from services.settlement_service import SettlementService

from .helpers import create_users_and_room


async def test_full_room_financial_flow(session):
    # --------------------------------
    # СОЗДАЁМ КОМНАТУ И 2 УЧАСТНИКОВ
    # --------------------------------

    users, room, members = await create_users_and_room(
        session,
        count=2,
    )

    payer = users[0]
    debtor = users[1]

    # --------------------------------
    # ДОБАВЛЯЕМ ЧЕК
    # --------------------------------

    receipt = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="test.jpg",
        total=100.0,
    )

    await session.commit()

    assert receipt.id is not None
    assert receipt.total == 100.0

    # --------------------------------
    # ДОБАВЛЯЕМ ПЛАТЁЖ
    # --------------------------------

    payment = await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=payer.id,
        amount=100.0,
        description="Dinner",
    )

    await session.commit()

    assert payment.id is not None
    assert payment.amount == 100.0
    assert payment.user_id == payer.id

    # --------------------------------
    # ПОЛУЧАЕМ ПЛАТЕЖИ
    # --------------------------------

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    assert len(payments) == 1

    # --------------------------------
    # СНАЧАЛА ДОЛГ ДОЛЖЕН СУЩЕСТВОВАТЬ
    # --------------------------------

    settlements = (
        await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room.id,
        )
    )

    details_before = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=settlements,
    )

    assert details_before["total"] == 100
    assert details_before["share"] == 50

    assert details_before["balances"][payer.id] == 50
    assert details_before["balances"][debtor.id] == -50

    assert details_before["transfers"] == [
        {
            "from_user_id": debtor.id,
            "to_user_id": payer.id,
            "amount": 50,
        }
    ]

    # --------------------------------
    # СОЗДАЁМ ПОГАШЕНИЕ
    # --------------------------------

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=debtor.id,
        to_user_id=payer.id,
        amount=50.0,
    )

    await session.commit()

    assert settlement is not None
    assert settlement.amount == 50.0
    assert settlement.from_user_id == debtor.id
    assert settlement.to_user_id == payer.id
    assert settlement.status == "pending"

    # --------------------------------
    # PENDING НЕ ДОЛЖЕН УБРАТЬ ДОЛГ
    # --------------------------------

    pending_settlements = (
        await SettlementService.get_pending_for_receiver(
            session=session,
            room_id=room.id,
            user_id=payer.id,
        )
    )

    assert len(pending_settlements) == 1
    assert pending_settlements[0].id == settlement.id

    confirmed_settlements = (
        await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room.id,
        )
    )

    details_pending = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    assert details_pending["balances"][payer.id] == 50
    assert details_pending["balances"][debtor.id] == -50

    # --------------------------------
    # ПОДТВЕРЖДАЕМ ПОГАШЕНИЕ
    # --------------------------------

    confirmed, status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=payer.id,
        )
    )

    await session.commit()

    assert confirmed is not None
    assert status == "confirmed"
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at is not None

    # --------------------------------
    # ПОЛУЧАЕМ ПОДТВЕРЖДЁННЫЕ ПОГАШЕНИЯ
    # --------------------------------

    confirmed_settlements = (
        await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room.id,
        )
    )

    assert len(confirmed_settlements) == 1
    assert confirmed_settlements[0].id == settlement.id

    # --------------------------------
    # ДОЛГ ДОЛЖЕН ИСЧЕЗНУТЬ
    # --------------------------------

    details_after = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    assert details_after["balances"][payer.id] == 0
    assert details_after["balances"][debtor.id] == 0

    assert details_after["transfers"] == []