import pytest

pytest.importorskip("aiosqlite")

from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from services.room_member_service import (
    RoomMemberService,
)

from .helpers import create_users_and_room


async def test_member_can_manage_receipts(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await ReceiptPermissionService.can_manage(
        session=session,
        room_id=room.id,
        user_id=users[1].id,
    )

    assert result == ReceiptPermission.ALLOWED


async def test_non_member_cannot_manage_receipts(session):
    _, room, _ = await create_users_and_room(
        session,
        count=1,
    )

    from database.models import User

    stranger = User(
        telegram_id=99999,
        first_name="Stranger",
    )

    session.add(stranger)
    await session.flush()

    result = await ReceiptPermissionService.can_manage(
        session=session,
        room_id=room.id,
        user_id=stranger.id,
    )

    assert result == ReceiptPermission.NOT_MEMBER


async def test_missing_room_denies_receipt_access(session):
    users, _, _ = await create_users_and_room(
        session,
        count=1,
    )

    result = await ReceiptPermissionService.can_manage(
        session=session,
        room_id=999999,
        user_id=users[0].id,
    )

    assert result == ReceiptPermission.NOT_MEMBER


async def test_removed_member_cannot_manage_receipts(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    member = users[1]

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert removed is True

    await session.commit()

    result = await ReceiptPermissionService.can_manage(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert result == ReceiptPermission.NOT_MEMBER