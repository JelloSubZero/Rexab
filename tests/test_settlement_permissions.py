import pytest

pytest.importorskip("aiosqlite")

from services.settlement_permission_service import (
    SettlementPermission,
    SettlementPermissionService,
)
from services.settlement_service import SettlementService
from services.room_member_service import RoomMemberService

from .helpers import create_users_and_room


# ============================================================
# CREATE SETTLEMENT
# ============================================================


async def test_member_can_create_settlement(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await SettlementPermissionService.can_create(
        session=session,
        room_id=room.id,
        actor_user_id=users[1].id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
    )

    assert result == SettlementPermission.ALLOWED


async def test_non_member_cannot_create_settlement(session):
    _, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    from database.models import User

    stranger = User(
        telegram_id=99999,
        first_name="Stranger",
    )

    session.add(stranger)
    await session.flush()

    result = await SettlementPermissionService.can_create(
        session=session,
        room_id=room.id,
        actor_user_id=stranger.id,
        from_user_id=stranger.id,
        to_user_id=1,
    )

    assert result == SettlementPermission.NOT_MEMBER


async def test_debtor_must_be_room_member(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    from database.models import User

    stranger = User(
        telegram_id=99998,
        first_name="Stranger",
    )

    session.add(stranger)
    await session.flush()

    result = await SettlementPermissionService.can_create(
        session=session,
        room_id=room.id,
        actor_user_id=users[0].id,
        from_user_id=stranger.id,
        to_user_id=users[0].id,
    )

    assert result == SettlementPermission.DEBTOR_NOT_MEMBER


async def test_receiver_must_be_room_member(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    from database.models import User

    stranger = User(
        telegram_id=99997,
        first_name="Stranger",
    )

    session.add(stranger)
    await session.flush()

    result = await SettlementPermissionService.can_create(
        session=session,
        room_id=room.id,
        actor_user_id=users[0].id,
        from_user_id=users[1].id,
        to_user_id=stranger.id,
    )

    assert result == SettlementPermission.RECEIVER_NOT_MEMBER


async def test_user_cannot_create_settlement_to_self(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await SettlementPermissionService.can_create(
        session=session,
        room_id=room.id,
        actor_user_id=users[0].id,
        from_user_id=users[0].id,
        to_user_id=users[0].id,
    )

    assert result == SettlementPermission.SAME_USER


# ============================================================
# CONFIRM SETTLEMENT
# ============================================================


async def test_receiver_can_confirm_settlement(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=50.0,
    )

    await session.commit()

    result = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=room.id,
        settlement_id=settlement.id,
        actor_user_id=users[0].id,
    )

    assert result == SettlementPermission.ALLOWED


async def test_non_receiver_cannot_confirm_settlement(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=users[0].id,
        amount=50.0,
    )

    await session.commit()

    result = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=room.id,
        settlement_id=settlement.id,
        actor_user_id=users[1].id,
    )

    assert result == SettlementPermission.NOT_RECEIVER


async def test_missing_settlement_cannot_be_confirmed(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=room.id,
        settlement_id=999999,
        actor_user_id=users[0].id,
    )

    assert result == SettlementPermission.SETTLEMENT_NOT_FOUND


async def test_settlement_from_another_room_is_rejected(session):
    users1, room1, _ = await create_users_and_room(
        session,
        count=2,
        telegram_id_start=1000,
    )

    users2, room2, _ = await create_users_and_room(
        session,
        count=2,
        telegram_id_start=2000,
    )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room2.id,
        from_user_id=users2[1].id,
        to_user_id=users2[0].id,
        amount=75.0,
    )

    await session.commit()

    result = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=room1.id,
        settlement_id=settlement.id,
        actor_user_id=users1[0].id,
    )

    assert result == SettlementPermission.WRONG_ROOM


async def test_removed_receiver_cannot_confirm_settlement(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    receiver = users[0]

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=users[1].id,
        to_user_id=receiver.id,
        amount=50.0,
    )

    await session.commit()

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room.id,
        user_id=receiver.id,
    )

    assert removed is True

    await session.commit()

    result = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=room.id,
        settlement_id=settlement.id,
        actor_user_id=receiver.id,
    )

    assert result == SettlementPermission.NOT_MEMBER