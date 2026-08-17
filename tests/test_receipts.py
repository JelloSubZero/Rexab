import pytest

pytest.importorskip("aiosqlite")

from services.receipt_service import ReceiptService

from .helpers import create_users_and_room


async def test_create_receipt(session):
    users, room, _ = await create_users_and_room(session)

    receipt = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="static/receipts/test.jpg",
        total=125.50,
    )

    await session.commit()

    assert receipt.id is not None
    assert receipt.room_id == room.id
    assert receipt.photo_path == "static/receipts/test.jpg"
    assert receipt.total == 125.50


async def test_get_receipt_by_id(session):
    _, room, _ = await create_users_and_room(session)

    created = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="test.jpg",
        total=100.0,
    )

    await session.commit()

    receipt = await ReceiptService.get_receipt(
        session=session,
        receipt_id=created.id,
    )

    assert receipt is not None
    assert receipt.id == created.id
    assert receipt.total == 100.0


async def test_update_receipt_total(session):
    _, room, _ = await create_users_and_room(session)

    receipt = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="test.jpg",
        total=None,
    )

    await session.commit()

    updated = await ReceiptService.update_total(
        session=session,
        receipt_id=receipt.id,
        total=333.33,
    )

    await session.commit()

    assert updated is not None
    assert updated.id == receipt.id
    assert updated.total == 333.33

    stored = await ReceiptService.get_receipt(
        session=session,
        receipt_id=receipt.id,
    )

    assert stored is not None
    assert stored.total == 333.33


async def test_room_total(session):
    _, room, _ = await create_users_and_room(session)

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="receipt_1.jpg",
        total=100.0,
    )

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="receipt_2.jpg",
        total=250.50,
    )

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="receipt_3.jpg",
        total=None,
    )

    await session.commit()

    total = await ReceiptService.get_room_total(
        session=session,
        room_id=room.id,
    )

    assert total == 350.50


async def test_delete_receipt(session):
    _, room, _ = await create_users_and_room(session)

    receipt = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path="test.jpg",
        total=75.0,
    )

    await session.commit()

    deleted = await ReceiptService.delete_receipt(
        session=session,
        receipt_id=receipt.id,
    )

    await session.commit()

    assert deleted is True

    stored = await ReceiptService.get_receipt(
        session=session,
        receipt_id=receipt.id,
    )

    assert stored is None


async def test_delete_missing_receipt(session):
    deleted = await ReceiptService.delete_receipt(
        session=session,
        receipt_id=999999,
    )

    assert deleted is False