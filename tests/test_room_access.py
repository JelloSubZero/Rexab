import pytest

pytest.importorskip("aiosqlite")

from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService

from .helpers import create_users_and_room


async def test_member_has_access_to_room(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    owner = users[0]
    member = users[1]

    owner_access = await RoomAccessService.check_access(
        session=session,
        room_id=room.id,
        user_id=owner.id,
    )

    member_access = await RoomAccessService.check_access(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert owner_access is True
    assert member_access is True


async def test_non_member_has_no_access(session):
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

    access = await RoomAccessService.check_access(
        session=session,
        room_id=room.id,
        user_id=stranger.id,
    )

    assert access is False


async def test_removed_member_loses_access(session):
    users, room, _ = await create_users_and_room(
        session,
        count=2,
    )

    member = users[1]

    before = await RoomAccessService.check_access(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert before is True

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert removed is True

    await session.commit()

    after = await RoomAccessService.check_access(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert after is False


async def test_removed_member_is_not_member(session):
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

    is_member = await RoomMemberService.is_member(
        session=session,
        room_id=room.id,
        user_id=member.id,
    )

    assert is_member is False