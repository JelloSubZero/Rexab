import pytest

pytest.importorskip("aiosqlite")

from database.models import User
from services.room_member_service import RoomMemberService

from .helpers import create_users_and_room


async def test_add_member(session):
    _, room, _ = await create_users_and_room(
        session,
        count=1,
    )

    new_user = User(
        telegram_id=9999,
        first_name="New User",
    )

    session.add(new_user)
    await session.flush()

    member = await RoomMemberService.join_room(
        session=session,
        room_id=room.id,
        user_id=new_user.id,
    )

    await session.commit()

    assert member is not None
    assert member.room_id == room.id
    assert member.user_id == new_user.id

    is_member = await RoomMemberService.is_member(
        session=session,
        room_id=room.id,
        user_id=new_user.id,
    )

    assert is_member is True


async def test_join_existing_member_returns_none(session):
    users, room, _ = await create_users_and_room(
        session,
        count=1,
    )

    result = await RoomMemberService.join_room(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
    )

    assert result is None


async def test_remove_member(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    user = users[1]

    assert await RoomMemberService.is_member(
        session=session,
        room_id=room.id,
        user_id=user.id,
    )

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room.id,
        user_id=user.id,
    )

    await session.commit()

    assert removed is True

    is_member = await RoomMemberService.is_member(
        session=session,
        room_id=room.id,
        user_id=user.id,
    )

    assert is_member is False


async def test_remove_missing_member_returns_false(session):
    _, room, _ = await create_users_and_room(
        session,
        count=1,
    )

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room.id,
        user_id=999999,
    )

    assert removed is False