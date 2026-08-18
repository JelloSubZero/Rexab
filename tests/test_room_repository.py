import pytest

pytest.importorskip("aiosqlite")

from sqlalchemy import select

from database.models import (
    Receipt,
    RoomMember,
    RoomPayment,
    RoomView,
)

from repositories.room_repository import RoomRepository

from .helpers import create_users_and_room


async def test_create_room(session):
    users, _, _ = await create_users_and_room(
        session,
        count=1,
    )

    room = await RoomRepository.create(
        session=session,
        owner_id=users[0].id,
        code="NEWT001",
    )

    assert room.id is not None
    assert room.owner_id == users[0].id
    assert room.code == "NEWT001"

    await session.commit()

    stored = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )

    assert stored is not None
    assert stored.id == room.id
    assert stored.code == "NEWT001"


async def test_delete_room_removes_room_data(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    # Дополнительные данные комнаты

    receipt = Receipt(
        room_id=room.id,
        photo_path="test.jpg",
        total=100.0,
    )

    payment = RoomPayment(
        room_id=room.id,
        user_id=users[0].id,
        amount=100.0,
        description="Dinner",
    )

    view = RoomView(
        room_id=room.id,
        user_id=users[0].id,
        chat_id=123456,
        message_id=999,
    )

    session.add_all([
        receipt,
        payment,
        view,
    ])

    await session.flush()

    deleted = await RoomRepository.delete(
        session=session,
        room_id=room.id,
    )

    assert deleted is True

    await session.commit()

    # Комната удалена

    room_result = await session.execute(
        select(RoomView).where(
            RoomView.room_id == room.id
        )
    )

    assert room_result.scalars().all() == []

    # Участники удалены

    members_result = await session.execute(
        select(RoomMember).where(
            RoomMember.room_id == room.id
        )
    )

    assert members_result.scalars().all() == []

    # Платежи удалены

    payments_result = await session.execute(
        select(RoomPayment).where(
            RoomPayment.room_id == room.id
        )
    )

    assert payments_result.scalars().all() == []

    # Чеки удалены

    receipts_result = await session.execute(
        select(Receipt).where(
            Receipt.room_id == room.id
        )
    )

    assert receipts_result.scalars().all() == []

    # Сама комната удалена

    stored_room = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )

    assert stored_room is None


async def test_delete_missing_room_returns_false(session):
    deleted = await RoomRepository.delete(
        session=session,
        room_id=999999,
    )

    assert deleted is False