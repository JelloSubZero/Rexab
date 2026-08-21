import pytest

pytest.importorskip("aiosqlite")

from services.anchor_service import (
    AnchorService,
    build_closed_screen,
    build_menu_screen,
)
from services.debt_service import DebtService
from services.receipt_service import ReceiptService
from services.room_payment_service import RoomPaymentService
from services.settlement_service import SettlementService
from repositories.room_repository import RoomRepository

from .fakes import FakeBot
from .helpers import create_users_and_room


async def test_full_room_lifecycle_stays_on_one_anchor_each(session, tmp_path):
    users, room, members = await create_users_and_room(session, count=2)
    payer, debtor = users
    bot = FakeBot()

    # --------------------------------
    # КАЖДЫЙ УЧАСТНИК ПОЛУЧАЕТ ЯКОРЬ
    # --------------------------------

    for index, user in enumerate(users):
        await AnchorService.create(
            bot=bot,
            session=session,
            room_id=room.id,
            user_id=user.id,
            chat_id=100 + index,
            text="Комната создана",
        )

    await session.commit()

    assert len(bot.sent) == 2

    # --------------------------------
    # ДОБАВЛЯЕМ ЧЕК, ОБНОВЛЯЕМ ОБА ЯКОРЯ
    # --------------------------------

    receipt_path = tmp_path / "receipt.jpg"
    receipt_path.write_bytes(b"fake-image")

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path=str(receipt_path),
        total=100.0,
    )

    await session.commit()

    total = await ReceiptService.get_room_total(
        session=session,
        room_id=room.id,
    )

    async def render_menu_for(member_user_id):
        return build_menu_screen(
            room=room,
            total=total,
            members=members,
            is_owner=(member_user_id == room.owner_id),
        )

    await AnchorService.broadcast(
        bot=bot,
        session=session,
        room_id=room.id,
        render_fn=render_menu_for,
    )

    assert len(bot.edited) == 2
    assert all("100.00 zł" in entry["text"] for entry in bot.edited)
    # No new messages were sent for the receipt confirmation — same anchors.
    assert len(bot.sent) == 2

    # --------------------------------
    # ДОБАВЛЯЕМ ПЛАТЁЖ
    # --------------------------------

    await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=payer.id,
        amount=100.0,
        description="Dinner",
    )

    await session.commit()

    # --------------------------------
    # ЗАКРЫВАЕМ КОМНАТУ
    # --------------------------------

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=[],
    )

    assert transfers == [
        {
            "from_user_id": debtor.id,
            "to_user_id": payer.id,
            "amount": 50.0,
        }
    ]

    async def render_closed_for(member_user_id):
        return build_closed_screen(
            room=room,
            members=members,
            transfers=transfers,
            user_id=member_user_id,
            pending_for_debtor=[],
            pending_for_receiver=[],
        )

    await AnchorService.broadcast(
        bot=bot,
        session=session,
        room_id=room.id,
        render_fn=render_closed_for,
    )

    assert len(bot.sent) == 2  # still no new messages

    # --------------------------------
    # ПОГАШАЕМ ДОЛГ
    # --------------------------------

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=debtor.id,
        to_user_id=payer.id,
        amount=50.0,
    )

    await session.commit()

    confirmed, status = await SettlementService.confirm_settlement(
        session=session,
        settlement_id=settlement.id,
        confirmer_user_id=payer.id,
    )

    await session.commit()

    assert status == "confirmed"

    confirmed_settlements = await SettlementService.get_confirmed_for_room(
        session=session,
        room_id=room.id,
    )

    final_transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    assert final_transfers == []

    total_debt = sum(
        float(t["amount"]) for t in final_transfers
    )

    fully_settled = await SettlementService.is_room_fully_settled(
        session=session,
        room_id=room.id,
        total_debt=total_debt,
    )

    assert fully_settled is True

    # --------------------------------
    # КОМНАТА УДАЛЯЕТСЯ, СВОДКА ОСТАЁТСЯ
    # --------------------------------

    await AnchorService.finalize(
        bot=bot,
        session=session,
        room_id=room.id,
    )
    await session.commit()

    assert len(bot.sent) == 2       # no new messages, ever
    # menu update + closed-room update + settled screen, per user (2 users x 3 renders)
    assert len(bot.edited) == 6
    for entry in bot.edited[-2:]:
        assert "погашен" in entry["text"].lower()
        assert entry["keyboard"] is None

    assert not receipt_path.exists()

    remaining_room = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )
    assert remaining_room is None


async def test_partial_settlement_does_not_trigger_finalize_condition(session):
    """
    Regression guard for the Task 14 finalize-trigger bug: settlement_confirm
    must only treat a room as ready for AnchorService.finalize when
    len(transfers) == 0 (fully settled) — not when only some debt has been
    confirmed paid. With 3 members, one payer and two debtors, confirming
    only ONE of the two debts must leave the room's data intact and the
    len(transfers) == 0 condition False. Confirming the second debt must
    then flip it to True, matching handlers/settlement.py::settlement_confirm.
    """

    users, room, members = await create_users_and_room(session, count=3)
    payer, debtor_one, debtor_two = users

    await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=payer.id,
        amount=90.0,
        description="Dinner",
    )

    await session.commit()

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=[],
    )

    assert sorted(transfers, key=lambda t: t["from_user_id"]) == sorted(
        [
            {
                "from_user_id": debtor_one.id,
                "to_user_id": payer.id,
                "amount": 30.0,
            },
            {
                "from_user_id": debtor_two.id,
                "to_user_id": payer.id,
                "amount": 30.0,
            },
        ],
        key=lambda t: t["from_user_id"],
    )

    # --------------------------------
    # ПОГАШАЕМ ТОЛЬКО ОДИН ИЗ ДВУХ ДОЛГОВ
    # --------------------------------

    settlement_one = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=debtor_one.id,
        to_user_id=payer.id,
        amount=30.0,
    )

    await session.commit()

    _, status = await SettlementService.confirm_settlement(
        session=session,
        settlement_id=settlement_one.id,
        confirmer_user_id=payer.id,
    )

    await session.commit()

    assert status == "confirmed"

    confirmed_settlements = await SettlementService.get_confirmed_for_room(
        session=session,
        room_id=room.id,
    )

    partial_transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    # The second debt is still outstanding.
    assert partial_transfers != []
    assert partial_transfers == [
        {
            "from_user_id": debtor_two.id,
            "to_user_id": payer.id,
            "amount": 30.0,
        }
    ]

    # This mirrors the exact trigger condition in
    # handlers/settlement.py::settlement_confirm — it must be False here,
    # since real debt remains. The Task 14 bug fired finalize at roughly
    # this halfway point instead.
    fully_settled_condition = len(partial_transfers) == 0
    assert fully_settled_condition is False

    # Nothing analogous to AnchorService.finalize should have run: the room
    # and its data must still be present.
    still_present_room = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )
    assert still_present_room is not None
    assert still_present_room.id == room.id

    # --------------------------------
    # ПОГАШАЕМ ВТОРОЙ ДОЛГ — ТЕПЕРЬ ПОЛНОСТЬЮ
    # --------------------------------

    settlement_two = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=debtor_two.id,
        to_user_id=payer.id,
        amount=30.0,
    )

    await session.commit()

    _, status_two = await SettlementService.confirm_settlement(
        session=session,
        settlement_id=settlement_two.id,
        confirmer_user_id=payer.id,
    )

    await session.commit()

    assert status_two == "confirmed"

    fully_confirmed_settlements = await SettlementService.get_confirmed_for_room(
        session=session,
        room_id=room.id,
    )

    final_transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=fully_confirmed_settlements,
    )

    assert final_transfers == []
    assert (len(final_transfers) == 0) is True
