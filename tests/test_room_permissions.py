import pytest

pytest.importorskip("aiosqlite")

from services.room_permission_service import (
    RemoveMemberPermission,
    RoomPermissionService,
)

from .helpers import create_users_and_room


async def test_owner_can_remove_member(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await RoomPermissionService.can_remove_member(
        session=session,
        room_id=room.id,
        actor_user_id=users[0].id,
        target_user_id=users[1].id,
    )

    assert result == RemoveMemberPermission.ALLOWED


async def test_member_cannot_remove_member(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await RoomPermissionService.can_remove_member(
        session=session,
        room_id=room.id,
        actor_user_id=users[1].id,
        target_user_id=users[0].id,
    )

    assert result == RemoveMemberPermission.NOT_OWNER


async def test_owner_cannot_remove_self(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await RoomPermissionService.can_remove_member(
        session=session,
        room_id=room.id,
        actor_user_id=users[0].id,
        target_user_id=users[0].id,
    )

    assert result == (
        RemoveMemberPermission.OWNER_CANNOT_BE_REMOVED
    )


async def test_remove_member_from_missing_room(session):
    users, _, _ = await create_users_and_room(
        session,
        count=2,
    )

    result = await RoomPermissionService.can_remove_member(
        session=session,
        room_id=999999,
        actor_user_id=users[0].id,
        target_user_id=users[1].id,
    )

    assert result == RemoveMemberPermission.ROOM_NOT_FOUND