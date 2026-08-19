import pytest

pytest.importorskip("aiosqlite")

from services.payment_permission_service import (
    PaymentPermission,
    PaymentPermissionService,
)

from .helpers import create_users_and_room


async def test_member_can_manage_payments(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await PaymentPermissionService.can_manage(
        session=session,
        room_id=room.id,
        user_id=users[1].id,
    )

    assert result == PaymentPermission.ALLOWED


async def test_non_member_cannot_manage_payments(session):
    users, room, _ = await create_users_and_room(
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

    result = await PaymentPermissionService.can_manage(
        session=session,
        room_id=room.id,
        user_id=stranger.id,
    )

    assert result == PaymentPermission.NOT_MEMBER


async def test_missing_room_denies_payment_access(session):
    users, _, _ = await create_users_and_room(
        session,
        count=1,
    )

    result = await PaymentPermissionService.can_manage(
        session=session,
        room_id=999999,
        user_id=users[0].id,
    )

    assert result == PaymentPermission.NOT_MEMBER