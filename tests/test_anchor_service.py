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


async def test_broadcast_renders_every_room_view(session):
    users, room, _ = await create_users_and_room(session, count=2)
    bot = FakeBot()

    for index, user in enumerate(users):
        await AnchorService.create(
            bot=bot,
            session=session,
            room_id=room.id,
            user_id=user.id,
            chat_id=100 + index,
            text="initial",
        )

    await session.commit()

    seen_user_ids = []

    async def render_fn(user_id):
        seen_user_ids.append(user_id)
        return f"screen for {user_id}", None

    await AnchorService.broadcast(
        bot=bot,
        session=session,
        room_id=room.id,
        render_fn=render_fn,
    )

    assert sorted(seen_user_ids) == sorted(u.id for u in users)
    assert len(bot.edited) == 2
    edited_texts = {entry["text"] for entry in bot.edited}
    assert edited_texts == {
        f"screen for {users[0].id}",
        f"screen for {users[1].id}",
    }


async def test_ping_sends_a_plain_message(session):
    bot = FakeBot()

    await AnchorService.ping(
        bot=bot,
        chat_id=42,
        text="🔔 hi",
    )

    assert len(bot.sent) == 1
    assert bot.sent[0]["chat_id"] == 42
    assert bot.sent[0]["text"] == "🔔 hi"
    assert bot.sent[0]["keyboard"] is None


async def test_ping_swallows_send_failures(session):
    class ExplodingBot(FakeBot):
        async def send_message(self, *args, **kwargs):
            raise RuntimeError("network down")

    bot = ExplodingBot()

    # Must not raise.
    await AnchorService.ping(
        bot=bot,
        chat_id=42,
        text="🔔 hi",
    )


from services.anchor_service import (
    build_members_list_text,
    build_menu_screen,
    build_members_screen,
)


async def test_build_members_list_text_marks_the_owner(session):
    users, room, members = await create_users_and_room(session, count=2)

    text = build_members_list_text(members, room.owner_id)

    assert f"1. {users[0].first_name} 👑" in text
    assert f"2. {users[1].first_name}" in text
    assert "👑" not in text.splitlines()[1]


async def test_build_members_list_text_empty(session):
    assert build_members_list_text([], owner_id=1) == "Пока нет участников."


async def test_build_members_list_text_handles_member_with_no_user(session):
    users, room, members = await create_users_and_room(session, count=2)

    # Create a member-like object with user=None to simulate a deleted user
    class MemberWithoutUser:
        def __init__(self, user_id):
            self.user_id = user_id
            self.user = None

    # Construct a list: first real member, then member with no user, then another real member
    members_mixed = [
        members[0],
        MemberWithoutUser(user_id=999),
        members[1],
    ]

    text = build_members_list_text(members_mixed, owner_id=room.owner_id)

    # Check that first member (owner) is marked with crown
    assert f"1. {users[0].first_name} 👑" in text
    # Check that second member (no user) shows "Неизвестный"
    assert "2. Неизвестный\n" in text
    # Check that third member is displayed normally
    assert f"3. {users[1].first_name}" in text


async def test_build_menu_screen_contains_code_and_total(session):
    users, room, members = await create_users_and_room(session, count=2)

    text, keyboard = build_menu_screen(
        room=room,
        total=45.5,
        members=members,
        is_owner=True,
    )

    assert room.code in text
    assert "45.50 zł" in text
    assert "Участников: 2" in text
    assert keyboard is not None


async def test_build_menu_screen_includes_banner(session):
    users, room, members = await create_users_and_room(session, count=1)

    text, _ = build_menu_screen(
        room=room,
        total=10.0,
        members=members,
        is_owner=True,
        banner="✅ Чек добавлен: 10.00 zł",
    )

    assert text.startswith("✅ Чек добавлен: 10.00 zł")


async def test_build_members_screen(session):
    users, room, members = await create_users_and_room(session, count=2)

    text, keyboard = build_members_screen(room=room, members=members)

    assert "Участники комнаты" in text
    assert "Всего: <b>2</b>" in text
    assert keyboard is not None


from services.anchor_service import build_closed_screen, build_settled_screen


async def test_build_closed_screen_shows_only_the_users_debts(session):
    users, room, members = await create_users_and_room(session, count=3)
    payer, debtor, bystander = users

    transfers = [
        {"from_user_id": debtor.id, "to_user_id": payer.id, "amount": 50.0},
    ]

    text, keyboard = build_closed_screen(
        room=room,
        members=members,
        transfers=transfers,
        user_id=debtor.id,
        pending_for_debtor=[],
        pending_for_receiver=[],
    )

    assert "Комната закрыта" in text
    assert "50.00 zł" in text
    assert payer.first_name in text
    assert keyboard is not None

    text_bystander, _ = build_closed_screen(
        room=room,
        members=members,
        transfers=transfers,
        user_id=bystander.id,
        pending_for_debtor=[],
        pending_for_receiver=[],
    )

    assert "нет непогашенных долгов" in text_bystander


async def test_build_settled_screen_has_no_keyboard(session):
    text, keyboard = build_settled_screen()

    assert "погашен" in text.lower()
    assert keyboard is None
