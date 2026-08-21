import pytest

pytest.importorskip("aiosqlite")

from services.anchor_service import AnchorService
from repositories.room_view_repository import RoomViewRepository

from .fakes import FakeBot
from .helpers import create_users_and_room


async def test_create_sends_message_and_saves_room_view(session):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=555,
        text="hello",
    )
    await session.commit()

    assert len(bot.sent) == 1
    assert bot.sent[0]["chat_id"] == 555
    assert bot.sent[0]["text"] == "hello"

    view = await RoomViewRepository.get(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
    )

    assert view is not None
    assert view.chat_id == 555
    assert view.message_id == bot.sent[0]["message_id"]


async def test_render_edits_the_stored_anchor(session):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=555,
        text="hello",
    )
    await session.commit()

    message_id = bot.sent[0]["message_id"]

    await AnchorService.render(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        text="updated",
        keyboard="kb",
    )

    assert len(bot.edited) == 1
    assert bot.edited[0]["chat_id"] == 555
    assert bot.edited[0]["message_id"] == message_id
    assert bot.edited[0]["text"] == "updated"
    assert bot.edited[0]["keyboard"] == "kb"


async def test_render_ignores_message_not_modified(session):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=555,
        text="hello",
    )
    await session.commit()

    message_id = bot.sent[0]["message_id"]
    bot.fail_edit(
        555,
        message_id,
        message="Bad Request: message is not modified: specified new message content and reply markup are exactly the same",
    )

    await AnchorService.render(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        text="hello",
    )

    assert bot.edited == []
    assert len(bot.sent) == 1


async def test_render_falls_back_to_create_when_message_is_gone(session):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=555,
        text="hello",
    )
    await session.commit()

    old_message_id = bot.sent[0]["message_id"]
    bot.fail_edit(555, old_message_id)

    await AnchorService.render(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        text="recreated",
    )

    assert bot.edited == []
    assert len(bot.sent) == 2
    assert bot.sent[1]["text"] == "recreated"

    view = await RoomViewRepository.get(
        session=session,
        room_id=room.id,
        user_id=users[0].id,
    )

    assert view.message_id == bot.sent[1]["message_id"]


async def test_render_is_noop_without_a_stored_anchor(session):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.render(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        text="nothing to edit",
    )

    assert bot.sent == []
    assert bot.edited == []
