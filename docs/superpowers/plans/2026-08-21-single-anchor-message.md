# Single-anchor-message room flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Rexab Telegram bot so each participant sees exactly one editable message per room, from creation through automatic deletion once every debt is settled.

**Architecture:** A new `AnchorService` becomes the only module that calls `bot.send_message` / `edit_message_text` / `delete_message` for room-related content, tracking one Telegram message per (room, user) via the existing `RoomView` table. Handlers keep building screen text/keyboards but hand them to `AnchorService` instead of calling Telegram directly. QR-code invites, the separate settlement notification thread, and the `RoomMessage` bulk-cleanup table are all retired as no-longer-needed side channels.

**Tech Stack:** Python 3, aiogram 3.30, SQLAlchemy 2.0 (async), Alembic, pytest + pytest-asyncio, aiosqlite (in-memory test DB).

**Spec:** [docs/superpowers/specs/2026-08-21-single-anchor-message-design.md](../specs/2026-08-21-single-anchor-message-design.md)

## Global Constraints

- One Telegram message per (room, user) from room creation/join to settlement — never send a second message for a screen that already has an anchor.
- QR-code invites are removed entirely; invite screens show only the room code and a `t.me` deep link with a share-URL button.
- On full settlement: edit every participant's anchor to a terminal summary (no keyboard), delete receipt files from disk, then cascade-delete the room's DB rows. Chat messages are never deleted, only edited.
- Settlement create/confirm re-render the existing anchors of both parties (never spawn a new message with buttons) and additionally send one button-less `AnchorService.ping` so the counterparty gets a push notification.
- `RoomMessageService` / `RoomMessage` model are fully retired — nothing in the new flow needs bulk message tracking.
- All business logic (permissions, `DebtService`, `SplitBillService`, `SettlementService`, OCR) is unchanged — only how results reach Telegram changes.
- Every new/changed piece of logic gets a test using the project's existing `tests/conftest.py::session` (in-memory SQLite) fixture and `tests/helpers.py::create_users_and_room`, plus the new `tests/fakes.py::FakeBot` for anything that talks to Telegram.

---

### Task 1: Test fakes for Telegram calls

**Files:**
- Create: `tests/fakes.py`

**Interfaces:**
- Produces: `FakeBot` — a stand-in for `aiogram.Bot` used by every later test that exercises `AnchorService` or a handler. Records calls instead of making network requests.
  - `FakeBot().sent: list[dict]` — appended by `send_message`, each `{"chat_id", "message_id", "text", "keyboard"}`.
  - `FakeBot().edited: list[dict]` — appended by `edit_message_text`, each `{"chat_id", "message_id", "text", "keyboard"}`.
  - `FakeBot().deleted: list[tuple[int, int]]` — appended by `delete_message`, each `(chat_id, message_id)`.
  - `FakeBot().fail_edit(chat_id, message_id, message="Bad Request: message to edit not found")` — makes the next `edit_message_text` for that `(chat_id, message_id)` raise `aiogram.exceptions.TelegramBadRequest`.
  - `async def send_message(chat_id, text, parse_mode=None, reply_markup=None, **kwargs)` → object with `.chat.id` and `.message_id`.
  - `async def edit_message_text(chat_id, message_id, text, parse_mode=None, reply_markup=None, **kwargs)`.
  - `async def delete_message(chat_id, message_id)`.

- [ ] **Step 1: Write `tests/fakes.py`**

```python
from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest


class FakeBot:

    def __init__(self):
        self.sent = []
        self.edited = []
        self.deleted = []
        self._next_message_id = 1000
        self._edit_failures = {}

    def fail_edit(
        self,
        chat_id,
        message_id,
        message="Bad Request: message to edit not found",
    ):
        self._edit_failures[(chat_id, message_id)] = message

    async def send_message(
        self,
        chat_id,
        text,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ):
        self._next_message_id += 1
        message_id = self._next_message_id

        self.sent.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "keyboard": reply_markup,
        })

        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=message_id,
        )

    async def edit_message_text(
        self,
        chat_id,
        message_id,
        text,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ):
        key = (chat_id, message_id)

        if key in self._edit_failures:
            error_message = self._edit_failures.pop(key)
            raise TelegramBadRequest(
                method=None,
                message=error_message,
            )

        self.edited.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "keyboard": reply_markup,
        })

        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=message_id,
        )

    async def delete_message(self, chat_id, message_id):
        self.deleted.append((chat_id, message_id))
```

- [ ] **Step 2: Sanity-check the fake in a scratch shell**

Run:
```bash
.venv/Scripts/python.exe -c "
import asyncio
from tests.fakes import FakeBot

async def main():
    bot = FakeBot()
    msg = await bot.send_message(chat_id=1, text='hi')
    print(msg.message_id, bot.sent)
    await bot.edit_message_text(chat_id=1, message_id=msg.message_id, text='bye')
    print(bot.edited)
    bot.fail_edit(1, msg.message_id)
    try:
        await bot.edit_message_text(chat_id=1, message_id=msg.message_id, text='fail')
    except Exception as e:
        print(type(e).__name__, e.message)

asyncio.run(main())
"
```
Expected: prints a message id, the `sent`/`edited` lists, then `TelegramBadRequest Bad Request: message to edit not found`.

- [ ] **Step 3: Commit**

```bash
git add tests/fakes.py
git commit -m "test: add FakeBot for anchor/handler tests"
```

---

### Task 2: `AnchorService.create` and `AnchorService.render`

**Files:**
- Create: `services/anchor_service.py`
- Test: `tests/test_anchor_service.py`

**Interfaces:**
- Consumes: `FakeBot` (Task 1), `RoomViewRepository` (`repositories/room_view_repository.py`, unchanged — `save(session, room_id, user_id, chat_id, message_id)`, `get(session, room_id, user_id)`, `get_all(session, room_id)`), `tests/helpers.py::create_users_and_room`.
- Produces:
  - `AnchorService.create(bot, session, room_id, user_id, chat_id, text, keyboard=None) -> Message`
  - `AnchorService.render(bot, session, room_id, user_id, text, keyboard=None) -> None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_anchor_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.anchor_service'`.

- [ ] **Step 3: Write `services/anchor_service.py`**

```python
import logging

from aiogram.exceptions import TelegramBadRequest

from repositories.room_view_repository import RoomViewRepository

logger = logging.getLogger(__name__)

_NOT_MODIFIED = "message is not modified"


class AnchorService:

    @staticmethod
    async def create(
        bot,
        session,
        room_id: int,
        user_id: int,
        chat_id: int,
        text: str,
        keyboard=None,
    ):
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        await RoomViewRepository.save(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )

        return message

    @staticmethod
    async def render(
        bot,
        session,
        room_id: int,
        user_id: int,
        text: str,
        keyboard=None,
    ):
        view = await RoomViewRepository.get(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if view is None:
            return

        try:
            await bot.edit_message_text(
                chat_id=view.chat_id,
                message_id=view.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        except TelegramBadRequest as error:

            if _NOT_MODIFIED in error.message:
                return

            logger.warning(
                "Anchor message unreachable for room %s user %s, "
                "recreating",
                room_id,
                user_id,
                exc_info=True,
            )

            await AnchorService.create(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=user_id,
                chat_id=view.chat_id,
                text=text,
                keyboard=keyboard,
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add services/anchor_service.py tests/test_anchor_service.py
git commit -m "feat: add AnchorService.create/render for single-anchor messages"
```

---

### Task 3: `AnchorService.broadcast` and `AnchorService.ping`

**Files:**
- Modify: `services/anchor_service.py`
- Test: `tests/test_anchor_service.py`

**Interfaces:**
- Consumes: `AnchorService.render` (Task 2), `RoomViewRepository.get_all(session, room_id)`.
- Produces:
  - `AnchorService.broadcast(bot, session, room_id, render_fn) -> None`, where `render_fn` is an **async** callable `(user_id: int) -> tuple[str, keyboard | None]`.
  - `AnchorService.ping(bot, chat_id, text) -> None` — fire-and-forget, never raises.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_anchor_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v -k "broadcast or ping"`
Expected: FAIL with `AttributeError: type object 'AnchorService' has no attribute 'broadcast'`.

- [ ] **Step 3: Add `broadcast` and `ping` to `services/anchor_service.py`**

Add inside the `AnchorService` class, after `render`:

```python
    @staticmethod
    async def broadcast(
        bot,
        session,
        room_id: int,
        render_fn,
    ):
        """render_fn: async (user_id: int) -> (text: str, keyboard)"""

        views = await RoomViewRepository.get_all(
            session=session,
            room_id=room_id,
        )

        for view in views:

            text, keyboard = await render_fn(view.user_id)

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=view.user_id,
                text=text,
                keyboard=keyboard,
            )

    @staticmethod
    async def ping(bot, chat_id: int, text: str):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
            )

        except Exception:
            logger.warning(
                "Failed to send ping to chat %s",
                chat_id,
                exc_info=True,
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add services/anchor_service.py tests/test_anchor_service.py
git commit -m "feat: add AnchorService.broadcast and AnchorService.ping"
```

---

### Task 4: Pure screen builders — menu and members

**Files:**
- Modify: `services/anchor_service.py`
- Test: `tests/test_anchor_service.py`

**Interfaces:**
- Consumes: `keyboards/room_menu.py::room_menu(room_id, is_owner=False)` (unchanged), `keyboards/room_members_menu.py::room_members_menu(room_id, members=None, owner_id=None)` (unchanged), ORM objects `Room`, `RoomMember` (`database/models.py`, unchanged).
- Produces (module-level functions in `services/anchor_service.py`, not methods on `AnchorService`):
  - `build_members_list_text(members, owner_id) -> str`
  - `build_menu_screen(room, total, members, is_owner, banner=None) -> tuple[str, InlineKeyboardMarkup]`
  - `build_members_screen(room, members) -> tuple[str, InlineKeyboardMarkup]`

These replace the near-identical member-list/menu text building duplicated today in `handlers/room.py::room_back`, `services/room_view_service.py::render`, `handlers/room_members.py`, and `handlers/receipt_callbacks.py::finish_receipts`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_anchor_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v -k build_`
Expected: FAIL with `ImportError: cannot import name 'build_members_list_text'`.

- [ ] **Step 3: Add the builders to `services/anchor_service.py`**

Add at module level (below the imports, above `class AnchorService`):

```python
from keyboards.room_menu import room_menu
from keyboards.room_members_menu import room_members_menu


def build_members_list_text(members, owner_id) -> str:

    lines = ""

    for index, member in enumerate(members, start=1):

        name = (
            member.user.first_name
            if member.user
            else "Неизвестный"
        )

        if member.user_id == owner_id:
            name += " 👑"

        lines += f"{index}. {name}\n"

    return lines or "Пока нет участников."


def build_menu_screen(room, total, members, is_owner, banner=None):

    banner_line = f"{banner}\n\n" if banner else ""
    members_text = build_members_list_text(members, room.owner_id)

    text = (
        f"{banner_line}"
        f"🏠 <b>{room.name or 'Комната'}</b>\n\n"
        f"🔑 Код:\n<code>{room.code}</code>\n\n"
        f"💰 Общая сумма:\n<b>{total:.2f} zł</b>\n\n"
        f"👥 Участников: {len(members)}\n\n"
        f"{members_text}"
    )

    return text, room_menu(room.id, is_owner=is_owner)


def build_members_screen(room, members):

    members_text = build_members_list_text(members, room.owner_id)

    text = (
        "👥 <b>Участники комнаты</b>\n\n"
        f"{members_text}\n"
        "───────────────\n"
        f"👥 Всего: <b>{len(members)}</b>"
    )

    return text, room_members_menu(
        room_id=room.id,
        members=members,
        owner_id=room.owner_id,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: PASS (13 tests).

- [ ] **Step 5: Commit**

```bash
git add services/anchor_service.py tests/test_anchor_service.py
git commit -m "feat: add build_menu_screen/build_members_screen pure builders"
```

---

### Task 5: Pure screen builders — closed room and settled room

**Files:**
- Modify: `services/anchor_service.py`
- Test: `tests/test_anchor_service.py`

**Interfaces:**
- Consumes: `keyboards/closed_room_menu.py::closed_room_menu(room_id, transfers=None, current_user_id=None, pending_for_debtor=None, pending_for_receiver=None)` (unchanged), `DebtService.calculate(members, payments, settlements)` (unchanged, `services/debt_service.py`) — transfer dicts shaped `{"from_user_id", "to_user_id", "amount"}`.
- Produces:
  - `build_closed_screen(room, members, transfers, user_id, pending_for_debtor, pending_for_receiver) -> tuple[str, InlineKeyboardMarkup]`
  - `build_settled_screen() -> tuple[str, None]`

This is a direct, behavior-preserving port of `services/room_view_service.py::render_closed`'s text/keyboard logic (the DB-fetching parts of `render_closed` stay in the handler that calls this — see Task 8).

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_anchor_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v -k "closed_screen or settled_screen"`
Expected: FAIL with `ImportError: cannot import name 'build_closed_screen'`.

- [ ] **Step 3: Add the builders to `services/anchor_service.py`**

```python
from keyboards.closed_room_menu import closed_room_menu


def build_closed_screen(
    room,
    members,
    transfers,
    user_id,
    pending_for_debtor,
    pending_for_receiver,
):

    user_transfers = [
        transfer
        for transfer in transfers
        if (
            transfer["from_user_id"] == user_id
            or transfer["to_user_id"] == user_id
        )
    ]

    total_debt = sum(
        float(transfer["amount"])
        for transfer in transfers
    )

    debts_text = ""

    for transfer in user_transfers:

        from_member = next(
            (m for m in members if m.user_id == transfer["from_user_id"]),
            None,
        )

        to_member = next(
            (m for m in members if m.user_id == transfer["to_user_id"]),
            None,
        )

        from_name = (
            from_member.user.first_name
            if from_member and from_member.user
            else "Неизвестный"
        )

        to_name = (
            to_member.user.first_name
            if to_member and to_member.user
            else "Неизвестный"
        )

        debts_text += (
            f"• <b>{from_name}</b> → <b>{to_name}</b>: "
            f"<b>{float(transfer['amount']):.2f} zł</b>\n"
        )

    if not debts_text:
        debts_text = "🎉 У вас нет непогашенных долгов."

    text = (
        "🔒 <b>Комната закрыта</b>\n\n"
        f"💰 Непогашено: <b>{total_debt:.2f} zł</b>\n"
        f"👥 Участников: <b>{len(members)}</b>\n\n"
        "👤 <b>Ваши долги</b>\n\n"
        f"{debts_text}"
    )

    keyboard = closed_room_menu(
        room_id=room.id,
        transfers=user_transfers,
        current_user_id=user_id,
        pending_for_debtor=pending_for_debtor,
        pending_for_receiver=pending_for_receiver,
    )

    return text, keyboard


def build_settled_screen():

    text = (
        "🎉 <b>Все долги погашены!</b>\n\n"
        "Комната закрыта и удалена. "
        "Спасибо, что пользовались Rexab!"
    )

    return text, None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: PASS (15 tests).

- [ ] **Step 5: Commit**

```bash
git add services/anchor_service.py tests/test_anchor_service.py
git commit -m "feat: add build_closed_screen/build_settled_screen pure builders"
```

---

### Task 6: `AnchorService.finalize`

**Files:**
- Modify: `services/anchor_service.py`
- Test: `tests/test_anchor_service.py`

**Interfaces:**
- Consumes: `build_settled_screen` (Task 5), `AnchorService.render` (Task 2), `RoomMemberService.get_members(session, room_id)` (unchanged), `ReceiptService.get_receipts(session, room_id)` (unchanged), `RoomService.delete_room(session, room_id) -> bool` (`services/room_service.py`, **unchanged, already cascades DB deletes** via `RoomRepository.delete`).
- Produces: `AnchorService.finalize(bot, session, room_id) -> None`.

`RoomService.delete_room` already deletes `RoomView`, `RoomMessage`, `RoomSettlement`, `RoomPayment`, `RoomHistory`, `Receipt`, `RoomMember`, then the `Room` row itself, all in one flush before commit (see `repositories/room_repository.py::delete`, lines 59-124). `finalize` only needs to add: editing every anchor to the terminal screen (before the `RoomView` rows are gone), and deleting receipt files from disk (using the paths fetched before `Receipt` rows are deleted).

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_anchor_service.py
import os

from services.receipt_service import ReceiptService
from services.room_service import RoomService
from repositories.room_repository import RoomRepository


async def test_finalize_edits_every_anchor_to_the_settled_screen(session, tmp_path):
    users, room, _ = await create_users_and_room(session, count=2)
    bot = FakeBot()

    for index, user in enumerate(users):
        await AnchorService.create(
            bot=bot,
            session=session,
            room_id=room.id,
            user_id=user.id,
            chat_id=100 + index,
            text="menu",
        )

    await session.commit()

    await AnchorService.finalize(
        bot=bot,
        session=session,
        room_id=room.id,
    )

    assert len(bot.edited) == 2
    for entry in bot.edited:
        assert "погашен" in entry["text"].lower()
        assert entry["keyboard"] is None


async def test_finalize_deletes_receipt_files_and_room_data(session, tmp_path):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=100,
        text="menu",
    )

    receipt_path = tmp_path / "receipt.jpg"
    receipt_path.write_bytes(b"fake-image")

    receipt = await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path=str(receipt_path),
        total=10.0,
    )

    await session.commit()

    await AnchorService.finalize(
        bot=bot,
        session=session,
        room_id=room.id,
    )
    await session.commit()

    assert not receipt_path.exists()

    remaining_room = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )
    assert remaining_room is None


async def test_finalize_continues_past_a_missing_receipt_file(session, tmp_path):
    users, room, _ = await create_users_and_room(session, count=1)
    bot = FakeBot()

    await AnchorService.create(
        bot=bot,
        session=session,
        room_id=room.id,
        user_id=users[0].id,
        chat_id=100,
        text="menu",
    )

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path=str(tmp_path / "does-not-exist.jpg"),
        total=10.0,
    )

    await session.commit()

    # Must not raise even though the file is missing.
    await AnchorService.finalize(
        bot=bot,
        session=session,
        room_id=room.id,
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v -k finalize`
Expected: FAIL with `AttributeError: type object 'AnchorService' has no attribute 'finalize'`.

- [ ] **Step 3: Add `finalize` to `services/anchor_service.py`**

Add `import os` and the following two imports to the top of the file (neither `services/receipt_service.py` nor `services/room_member_service.py` nor `services/room_service.py` imports `anchor_service`, so there's no circular-import risk):

```python
from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.room_service import RoomService
```

Then add inside the `AnchorService` class:

```python
    @staticmethod
    async def finalize(bot, session, room_id: int):

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        text, keyboard = build_settled_screen()

        for member in members:
            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member.user_id,
                text=text,
                keyboard=keyboard,
            )

        receipts = await ReceiptService.get_receipts(
            session=session,
            room_id=room_id,
        )

        for receipt in receipts:

            if not receipt.photo_path:
                continue

            try:
                os.remove(receipt.photo_path)

            except OSError:
                logger.warning(
                    "Failed to delete receipt file %s",
                    receipt.photo_path,
                    exc_info=True,
                )

        await RoomService.delete_room(
            session=session,
            room_id=room_id,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anchor_service.py -v`
Expected: PASS (18 tests).

- [ ] **Step 5: Commit**

```bash
git add services/anchor_service.py tests/test_anchor_service.py
git commit -m "feat: add AnchorService.finalize for room settlement cleanup"
```

---

### Task 7: Room creation and joining use the anchor

**Files:**
- Modify: `handlers/room.py:28-86` (`create_room`)
- Modify: `handlers/start.py`
- Test: none new (covered by Task 16's end-to-end test) — verify manually per Step 4 below.

**Interfaces:**
- Consumes: `AnchorService.create` (Task 2), `build_menu_screen` (Task 4).
- Produces: no new interfaces; removes the `RoomMessageService.save` call site in `create_room` and the `RoomViewService.show_room` call site in `start.py`.

- [ ] **Step 1: Rewrite `create_room` in `handlers/room.py`**

Replace lines 1-86 of `handlers/room.py` (imports through the end of `create_room`) with:

```python
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from services.room_member_service import RoomMemberService
from database.models import RoomStatus
from keyboards.room_close_confirm_menu import room_close_confirm_menu
from aiogram.exceptions import TelegramBadRequest

from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.room_service import RoomService
from services.anchor_service import (
    AnchorService,
    build_closed_screen,
    build_members_list_text,
    build_menu_screen,
)

from keyboards.room_menu import room_menu
from services.room_access_service import RoomAccessService
from services.room_permission_service import RoomPermissionService
from services.settlement_service import SettlementService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService

from states.receipt_state import ReceiptState

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "➕ Создать чек")
async def create_room(
    message: Message,
    state: FSMContext,
):
    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is None:
            await message.answer(
                "❌ Пользователь не найден. Выполните команду /start."
            )
            return

        room = await RoomService.create_room(
            session=session,
            owner_id=user.id,
        )

        await RoomMemberService.join_room(
            session=session,
            room_id=room.id,
            user_id=user.id,
        )

        await state.update_data(
            room_id=room.id,
        )

        await state.set_state(
            ReceiptState.waiting_receipt,
        )

        await AnchorService.create(
            bot=message.bot,
            session=session,
            room_id=room.id,
            user_id=user.id,
            chat_id=message.chat.id,
            text=(
                "🏠 <b>Комната создана</b>\n\n"
                f"🔑 Код комнаты:\n<code>{room.code}</code>\n\n"
                "📸 Отправьте первый чек.\n\n"
                "После загрузки чеков вы сможете "
                "пригласить участников."
            ),
        )

        await session.commit()
```

`build_closed_screen`, `build_members_list_text`, `SettlementService`, `RoomPaymentService`, and `DebtService` are imported here in preparation for Task 8, which rewrites the rest of this file (`room_back`, `room_close`, `room_close_confirm`) in place — leave the remaining functions in `handlers/room.py` untouched for now.

- [ ] **Step 2: Rewrite the join branch in `handlers/start.py`**

Modify `handlers/start.py:76-82`:

Before:
```python
            await RoomViewService.show_room(
                bot=message.bot,
                session=session,
                chat_id=message.chat.id,
                user_id=user.id,
                room_id=room.id,
            )
```

After:
```python
            total = await ReceiptService.get_room_total(
                session=session,
                room_id=room.id,
            )

            members = await RoomMemberService.get_members(
                session=session,
                room_id=room.id,
            )

            text, keyboard = build_menu_screen(
                room=room,
                total=total,
                members=members,
                is_owner=(room.owner_id == user.id),
            )

            await AnchorService.create(
                bot=message.bot,
                session=session,
                room_id=room.id,
                user_id=user.id,
                chat_id=message.chat.id,
                text=text,
                keyboard=keyboard,
            )

            async def render_menu_for(member_user_id):
                return build_menu_screen(
                    room=room,
                    total=total,
                    members=members,
                    is_owner=(member_user_id == room.owner_id),
                )

            await AnchorService.broadcast(
                bot=message.bot,
                session=session,
                room_id=room.id,
                render_fn=render_menu_for,
            )
```

Update the imports at the top of `handlers/start.py`:

Before:
```python
from services.room_view_service import RoomViewService
```

After:
```python
from services.anchor_service import AnchorService, build_menu_screen
from services.receipt_service import ReceiptService
```

(`RoomMemberService` is already imported in this file.)

- [ ] **Step 3: Run the full test suite to confirm nothing else broke**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS — these files aren't covered by existing tests, so this just confirms nothing else regressed and the module still imports cleanly. Add `.venv/Scripts/python.exe -c "import handlers.room, handlers.start"` to catch import errors specifically.

- [ ] **Step 4: Manual smoke test**

This task has no automated handler test yet (Task 16 adds one covering this exact path). For now, confirm by reading: `create_room` now calls `AnchorService.create` instead of `message.answer` + `RoomMessageService.save`, and `start.py`'s join branch now calls `AnchorService.create` + `AnchorService.broadcast` instead of `RoomViewService.show_room`. Both keep every other line (user lookup, `RoomMemberService.join_room`, `state` handling) unchanged.

- [ ] **Step 5: Commit**

```bash
git add handlers/room.py handlers/start.py
git commit -m "feat: create/join room via AnchorService instead of ad hoc messages"
```

---

### Task 8: Room menu, back, and close flow use the anchor

**Files:**
- Modify: `handlers/room_view.py`
- Modify: `handlers/room.py:88-407` (`room_back`, `room_close`, `room_close_confirm`)
- Test: `tests/test_anchor_service.py` stays as-is; this task is glue and is covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render`, `AnchorService.broadcast` (Task 2/3), `build_menu_screen` (Task 4), `build_closed_screen` (Task 5).
- Produces: removes the `RoomViewService` dependency from both files and the manual per-member `try/except TelegramBadRequest` loop in `room_close_confirm`; removes `RoomMessageService.delete_all` call.

- [ ] **Step 1: Rewrite `handlers/room_view.py`**

Replace the whole file:

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.room_access_service import RoomAccessService
from services.room_service import RoomService
from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen
from repositories.user_repository import UserRepository


router = Router()


@router.callback_query(
    F.data.startswith("room_view:")
)
async def room_view(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        text, keyboard = build_menu_screen(
            room=room,
            total=total or 0,
            members=members,
            is_owner=(room.owner_id == user.id),
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await callback.answer()
```

- [ ] **Step 2: Replace `room_back`, `room_close`, `room_close_confirm` in `handlers/room.py`**

Replace `handlers/room.py:88-407` (everything after `create_room`, to the end of the file) with:

```python
@router.callback_query(
    F.data.startswith("room_close:")
)
async def room_close(
    callback: CallbackQuery,
):

    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        is_owner = await RoomPermissionService.is_owner(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_owner:
            await callback.answer(
                "❌ Только владелец может закрыть комнату.",
                show_alert=True,
            )
            return

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=(
                "🔒 <b>Закрытие комнаты</b>\n\n"
                "Вы уверены, что хотите закрыть комнату?\n\n"
                "После закрытия новые участники "
                "не смогут присоединиться."
            ),
            keyboard=room_close_confirm_menu(
                room_id=room_id,
            ),
        )

        await session.commit()

    await callback.answer()


@router.callback_query(
    F.data.startswith("room_close_confirm:")
)
async def room_close_confirm(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        is_owner = await RoomPermissionService.is_owner(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_owner:
            await callback.answer(
                "❌ Только владелец может закрыть комнату.",
                show_alert=True,
            )
            return

        if room.status != RoomStatus.ACTIVE.value:
            await callback.answer(
                "❌ Комната уже закрыта.",
                show_alert=True,
            )
            return

        room.status = RoomStatus.CLOSED.value

        await session.commit()

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        async def render_closed_for(member_user_id):

            pending_for_debtor = (
                await SettlementService.get_pending_for_debtor(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            pending_for_receiver = (
                await SettlementService.get_pending_for_receiver(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            return build_closed_screen(
                room=room,
                members=members,
                transfers=transfers,
                user_id=member_user_id,
                pending_for_debtor=pending_for_debtor,
                pending_for_receiver=pending_for_receiver,
            )

        await AnchorService.broadcast(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            render_fn=render_closed_for,
        )

        await session.commit()

    await callback.answer(
        "✅ Комната закрыта"
    )
```

`handlers/room.py` no longer needs `room_menu`, `TelegramBadRequest`, or `logger` — leave the imports added in Task 7 as-is (unused imports here are harmless but if you prefer, drop `room_menu` and `TelegramBadRequest` from the import block; `logger` stays because it may still be useful for future error logging in this file).

- [ ] **Step 3: Run the test suite and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.room, handlers.room_view"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both imports succeed, full suite still passes.

- [ ] **Step 4: Commit**

```bash
git add handlers/room.py handlers/room_view.py
git commit -m "feat: route room menu/close/closed screens through AnchorService"
```

---

### Task 9: Invite screen without QR

**Files:**
- Modify: `handlers/room_invite.py`
- Delete: `services/qr_service.py`
- Modify: `config.py` (remove `QR_DIR`)
- Modify: `requirements.txt` (remove `qrcode`)
- Modify: `requirements-dev.txt` — n/a, no change needed.

**Interfaces:**
- Consumes: `AnchorService.render` (Task 2).
- Produces: no new interfaces; the `📤 Пригласить` button (`keyboards/room_menu.py:22-25`, unchanged) now leads to a text-only screen.

- [ ] **Step 1: Rewrite `handlers/room_invite.py`**

Replace the whole file:

```python
from urllib.parse import quote

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME
from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.room_access_service import RoomAccessService
from services.anchor_service import AnchorService

from repositories.user_repository import UserRepository


router = Router()


def build_invite_screen(room):

    invite_link = f"https://t.me/{BOT_USERNAME}?start={room.code}"

    share_text = (
        f"Присоединяйся к комнате в Rexab: {invite_link}"
    )

    share_url = (
        "https://t.me/share/url?"
        f"url={quote(invite_link, safe='')}"
        f"&text={quote(share_text, safe='')}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📤 Отправить другу",
        url=share_url,
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room.id}",
    )

    builder.adjust(1)

    text = (
        "📤 <b>Приглашение в комнату</b>\n\n"
        f"🔑 Код комнаты:\n<code>{room.code}</code>\n\n"
        "Отправьте другу ссылку или код."
    )

    return text, builder.as_markup()


@router.callback_query(
    F.data.startswith("room_invite:")
)
async def room_invite(
    callback: CallbackQuery,
):

    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        text, keyboard = build_invite_screen(room)

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await callback.answer()
```

- [ ] **Step 2: Delete `services/qr_service.py` and the `static/qr` directory**

```bash
git rm services/qr_service.py
rm -rf static/qr
```

- [ ] **Step 3: Remove `QR_DIR` from `config.py`**

Modify `config.py:24-31`:

Before:
```python
STATIC_DIR = BASE_DIR / "static"
QR_DIR = STATIC_DIR / "qr"
RECEIPTS_DIR = STATIC_DIR / "receipts"
LOGS_DIR = BASE_DIR / "logs"

# Автоматическое создание папок
QR_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

After:
```python
STATIC_DIR = BASE_DIR / "static"
RECEIPTS_DIR = STATIC_DIR / "receipts"
LOGS_DIR = BASE_DIR / "logs"

# Автоматическое создание папок
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Remove `qrcode` from `requirements.txt`**

Modify `requirements.txt:7` — delete the `qrcode==8.2` line.

- [ ] **Step 5: Verify nothing else references QR**

Run: `.venv/Scripts/python.exe -c "import handlers.room_invite, config"`

Then confirm no leftover references:
```bash
grep -ril "qr_service\|QR_DIR\|qrcode" --include="*.py" .
```
Expected: no output (aside from this plan file and the design spec, which are documentation, not code).

- [ ] **Step 6: Commit**

```bash
git add handlers/room_invite.py config.py requirements.txt
git rm services/qr_service.py
git add -A static/qr
git commit -m "feat: replace QR invite with text-only anchor screen"
```

---

### Task 10: Members screen uses the anchor

**Files:**
- Modify: `handlers/room_members.py`
- Test: covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render` (Task 2), `build_members_screen` (Task 4).

- [ ] **Step 1: Update `room_members` and `remove_member` in `handlers/room_members.py`**

Update imports (top of file):

Before:
```python
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from keyboards.room_members_menu import room_members_menu

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.room_access_service import RoomAccessService
from services.notification_service import NotificationService
from services.room_permission_service import (
    RemoveMemberPermission,
    RoomPermissionService,
)

from repositories.user_repository import UserRepository
```

After:
```python
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.room_access_service import RoomAccessService
from services.notification_service import NotificationService
from services.anchor_service import AnchorService, build_members_screen
from services.room_permission_service import (
    RemoveMemberPermission,
    RoomPermissionService,
)

from repositories.user_repository import UserRepository
```

Replace the tail of `room_members` (`handlers/room_members.py:93-137`, from the `# ПОЛУЧАЕМ УЧАСТНИКОВ` comment through the end of the function) with:

```python
        # --------------------------------
        # ПОЛУЧАЕМ УЧАСТНИКОВ
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        text, keyboard = build_members_screen(
            room=room,
            members=members,
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await callback.answer()
```

Replace the tail of `remove_member` (`handlers/room_members.py:293-353`, from `# ПОЛУЧАЕМ ОБНОВЛЁННЫЙ СПИСОК` through the end of the function) with:

```python
        # --------------------------------
        # ПОЛУЧАЕМ ОБНОВЛЁННЫЙ СПИСОК
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        text, keyboard = build_members_screen(
            room=room,
            members=members,
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await callback.answer(
        "✅ Участник удален."
    )
```

- [ ] **Step 2: Run tests and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.room_members"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both succeed.

- [ ] **Step 3: Commit**

```bash
git add handlers/room_members.py
git commit -m "feat: route members screen through AnchorService"
```

---

### Task 11: Receipt flow uses the anchor

**Files:**
- Modify: `handlers/receipt.py`
- Modify: `handlers/receipt_callbacks.py`
- Test: covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render`, `AnchorService.broadcast` (Task 2/3), `build_menu_screen` (Task 4).
- Produces: removes `RoomMessageService` usage from both files; the `add_receipt`/`finish_receipts` callbacks stop sending new messages.

- [ ] **Step 1: Rewrite `handlers/receipt.py`**

Update imports (top of file):

Before:
```python
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository

from services.room_view_service import RoomViewService
from services.room_message_service import RoomMessageService

from keyboards.receipt_menu import receipt_menu

from config import RECEIPTS_DIR

from database.session import AsyncSessionLocal

from services.receipt_service import ReceiptService
from services.ocr.ocr_service import OCRService

from states.receipt_state import ReceiptState
```

After:
```python
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen

from config import RECEIPTS_DIR

from database.session import AsyncSessionLocal

from services.receipt_service import ReceiptService
from services.ocr.ocr_service import OCRService

from states.receipt_state import ReceiptState
```

Replace `handlers/receipt.py:134-174` (the "ЕСЛИ СУММУ ОПРЕДЕЛИТЬ НЕ УДАЛОСЬ" branch) with:

```python
            # --------------------------------
            # ЕСЛИ СУММУ ОПРЕДЕЛИТЬ НЕ УДАЛОСЬ
            # --------------------------------

            if result.receipt.total is None:

                await session.commit()

                await state.update_data(
                    receipt_id=receipt.id,
                    room_id=room_id,
                )

                await state.set_state(
                    ReceiptState.waiting_total
                )

                await AnchorService.render(
                    bot=message.bot,
                    session=session,
                    room_id=room_id,
                    user_id=user.id,
                    text=(
                        "❌ Не удалось определить сумму чека.\n\n"
                        "Введите общую сумму вручную.\n\n"
                        "Например:\n"
                        "<code>123.45</code>"
                    ),
                )

                await session.commit()

            try:
                await message.delete()
            except Exception:
                logger.warning(
                    "Не удалось удалить сообщение с чеком",
                    exc_info=True,
                )

            if result.receipt.total is None:
                return
```

Replace `handlers/receipt.py:176-232` (the "ПОЛУЧАЕМ ОБЩУЮ СУММУ КОМНАТЫ" section through "СЛЕДУЮЩИЙ ЧЕК") with:

```python
            # --------------------------------
            # ОБНОВЛЯЕМ ЭКРАНЫ ВСЕХ УЧАСТНИКОВ
            # --------------------------------

            room = await RoomService.get_by_id(
                session=session,
                room_id=room_id,
            )

            room_total = await ReceiptService.get_room_total(
                session=session,
                room_id=room_id,
            )

            members = await RoomMemberService.get_members(
                session=session,
                room_id=room_id,
            )

            banner = (
                "✅ Чек добавлен: "
                f"{result.receipt.total:.2f} zł"
            )

            async def render_menu_for(member_user_id):
                return build_menu_screen(
                    room=room,
                    total=room_total,
                    members=members,
                    is_owner=(member_user_id == room.owner_id),
                    banner=banner if member_user_id == user.id else None,
                )

            await AnchorService.broadcast(
                bot=message.bot,
                session=session,
                room_id=room_id,
                render_fn=render_menu_for,
            )

            await session.commit()

        try:
            await message.delete()
        except Exception:
            logger.warning(
                "Не удалось удалить сообщение с чеком",
                exc_info=True,
            )

        # --------------------------------
        # СЛЕДУЮЩИЙ ЧЕК
        # --------------------------------

        await state.set_state(
            ReceiptState.waiting_receipt
        )
```

Now rewrite `manual_total` (`handlers/receipt.py:251-...` to the end of the file, i.e. everything after the `receipt_handler`'s `except Exception` block that follows it). Read the current tail of the file first — it continues past line 299 shown earlier with the amount parsing and the receipt update. Replace from `# ПОЛУЧАЕМ ДАННЫЕ FSM` (inside `manual_total`) through the end of the file with:

```python
    data = await state.get_data()

    receipt_id = data.get(
        "receipt_id"
    )

    room_id = data.get(
        "room_id"
    )

    if receipt_id is None or room_id is None:

        await message.answer(
            "❌ Чек не найден."
        )

        await state.clear()

        return

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is None:
            await message.answer(
                "❌ Пользователь не найден."
            )
            await state.clear()
            return

        await ReceiptService.update_total(
            session=session,
            receipt_id=receipt_id,
            total=total,
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        banner = f"✅ Чек добавлен: {total:.2f} zł"

        async def render_menu_for(member_user_id):
            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
                banner=banner if member_user_id == user.id else None,
            )

        await AnchorService.broadcast(
            bot=message.bot,
            session=session,
            room_id=room_id,
            render_fn=render_menu_for,
        )

        await session.commit()

    try:
        await message.delete()
    except Exception:
        logger.warning(
            "Не удалось удалить сообщение с суммой",
            exc_info=True,
        )

    await state.set_state(
        ReceiptState.waiting_receipt
    )
```

`keyboards/receipt_menu.py` and its "🧾 Добавить ещё чек" / "✅ Завершить добавление" buttons are no longer shown after a receipt — the menu screen with the updated total is the confirmation, and the room's normal menu buttons already cover everything the receipt menu offered. Leave `keyboards/receipt_menu.py` in place (Task 12 still wires its callbacks in `receipt_callbacks.py`) but it's no longer reachable from `receipt.py`; Step 2 below removes its call sites in `receipt_callbacks.py` too, so if you confirm nothing else references `receipt_menu`, delete `keyboards/receipt_menu.py` in Step 3.

- [ ] **Step 2: Rewrite `handlers/receipt_callbacks.py`**

Replace the whole file:

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from repositories.user_repository import UserRepository
from database.session import AsyncSessionLocal


from states.receipt_state import ReceiptState

from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)
from services.room_service import RoomService
from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen


router = Router()


@router.callback_query(
    F.data.startswith("add_receipt:")
)
async def add_receipt(
    callback: CallbackQuery,
    state: FSMContext,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        permission = (
            await ReceiptPermissionService.can_manage(
                session=session,
                room_id=room_id,
                user_id=user.id,
            )
        )

        if permission == ReceiptPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        await state.update_data(
            room_id=room_id,
        )

        await state.set_state(
            ReceiptState.waiting_receipt,
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=user.id,
            text="📷 Отправьте следующий чек.",
        )

        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("finish_receipts:"))
async def finish_receipts(
    callback: CallbackQuery,
    state: FSMContext,
):
    room_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            await state.clear()
            return

        permission = await ReceiptPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        if permission == ReceiptPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            await state.clear()
            return

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        text, keyboard = build_menu_screen(
            room=room,
            total=total or 0,
            members=members,
            is_owner=(room.owner_id == user.id),
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await state.clear()

    await callback.answer()
```

This also fixes a pre-existing bug: the old `finish_receipts` called `room_menu(room.id)` without `is_owner=`, so it always defaulted to `False` and hid the "🔒 Закрыть комнату" button from the owner. `build_menu_screen` computes `is_owner` correctly.

- [ ] **Step 3: Delete the now-unused receipt menu keyboard**

```bash
grep -ril "receipt_menu" --include="*.py" .
```
Expected: only `keyboards/receipt_menu.py` itself. If so:
```bash
git rm keyboards/receipt_menu.py
```

- [ ] **Step 4: Run tests and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.receipt, handlers.receipt_callbacks"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both succeed.

- [ ] **Step 5: Commit**

```bash
git add handlers/receipt.py handlers/receipt_callbacks.py
git rm -f keyboards/receipt_menu.py
git commit -m "feat: route receipt upload/manual-total flow through AnchorService"
```

---

### Task 12: Payments flow uses the anchor

**Files:**
- Modify: `handlers/payment.py`
- Test: covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render`, `AnchorService.broadcast` (Task 2/3), `build_menu_screen` (Task 4), the existing `_payments_text` (`handlers/payment.py:32-67`, unchanged) and `payment_manage_menu` (`keyboards/payment_manage_menu.py`, unchanged).

This file has 6 places that currently call `callback.message.edit_text`, `message.answer`, or `RoomMessageService.send`. Each gets the same substitution: build the same text/keyboard as today, then hand it to `AnchorService.render` (for the acting user) instead of sending/editing directly. Where a payment or deletion changes the room total, also `AnchorService.broadcast` the menu screen to the other members — this file currently does **not** refresh other members at all when a payment changes (unlike the receipt flow, which already does); this task fixes that inconsistency as part of the rewrite.

- [ ] **Step 1: Update imports**

Before (`handlers/payment.py:1-27`):
```python
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.payment_delete_menu import payment_delete_menu
from services.room_member_service import RoomMemberService
from services.room_history_service import RoomHistoryService
from services.notification_service import NotificationService
from services.room_message_service import RoomMessageService
from services.room_view_service import RoomViewService
from services.payment_permission_service import (
    PaymentPermission,
    PaymentPermissionService,
)


from database.session import AsyncSessionLocal
from services.split_bill_service import SplitBillService
from services.room_payment_service import RoomPaymentService

from repositories.user_repository import UserRepository

from states.payment_state import PaymentState
from services.debt_service import DebtService

from keyboards.payment_manage_menu import payment_manage_menu


router = Router()
```

After:
```python
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.payment_delete_menu import payment_delete_menu
from services.room_member_service import RoomMemberService
from services.room_history_service import RoomHistoryService
from services.notification_service import NotificationService
from services.room_service import RoomService
from services.receipt_service import ReceiptService
from services.anchor_service import AnchorService, build_menu_screen
from services.payment_permission_service import (
    PaymentPermission,
    PaymentPermissionService,
)


from database.session import AsyncSessionLocal
from services.split_bill_service import SplitBillService
from services.room_payment_service import RoomPaymentService

from repositories.user_repository import UserRepository

from states.payment_state import PaymentState
from services.debt_service import DebtService

from keyboards.payment_manage_menu import payment_manage_menu


router = Router()
```

- [ ] **Step 2: Route `payment_manage` through the anchor**

Replace `handlers/payment.py:365-425` (the whole `payment_manage` function body from `async with AsyncSessionLocal()` onward):

```python
    async with AsyncSessionLocal() as session:

        # Текущий пользователь
        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # Получаем платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = _payments_text(payments, split)

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

        await session.commit()

    await callback.answer()
```

- [ ] **Step 3: Route `payment_delete` (the confirmation prompt) through the anchor**

Replace `handlers/payment.py:135-150`:

Before:
```python
    await callback.message.edit_text(
        (
            "🗑 <b>Удалить платёж?</b>\n\n"
            f"💳 Плательщик: <b>{payer_name}</b>\n"
            f"💰 Сумма: <b>{amount:.2f} zł</b>\n"
            f"📝 Расход: <b>{description}</b>\n\n"
            "Вы уверены?"
        ),
        parse_mode="HTML",
        reply_markup=payment_delete_menu(
            payment_id=payment_id,
            room_id=room_id,
        ),
    )

    await callback.answer()
```

After:
```python
    async with AsyncSessionLocal() as session:

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=(
                "🗑 <b>Удалить платёж?</b>\n\n"
                f"💳 Плательщик: <b>{payer_name}</b>\n"
                f"💰 Сумма: <b>{amount:.2f} zł</b>\n"
                f"📝 Расход: <b>{description}</b>\n\n"
                "Вы уверены?"
            ),
            keyboard=payment_delete_menu(
                payment_id=payment_id,
                room_id=room_id,
            ),
        )

        await session.commit()

    await callback.answer()
```

(`current_user` is still in scope here from earlier in the function — no new lookup needed. This opens a second `AsyncSessionLocal()` block because the original code closed the first one via `async with` before this point; keep it that way rather than restructuring the whole function's session scope, to keep this change minimal and low-risk.)

- [ ] **Step 4: Route `payment_delete_confirm` through the anchor and broadcast to other members**

Replace `handlers/payment.py:340-363` (from `# ФОРМИРУЕМ ОБНОВЛЁННЫЙ СПИСОК` through the end of the function):

```python
    # --------------------------------
    # ФОРМИРУЕМ ОБНОВЛЁННЫЙ СПИСОК
    # --------------------------------

    async with AsyncSessionLocal() as session:

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = _payments_text(payments, split)

        await AnchorService.render(
            bot=bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        async def render_menu_for(member_user_id):
            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
            )

        for member in members:

            if member.user_id == current_user.id:
                continue

            text_for_member, keyboard_for_member = await render_menu_for(
                member.user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member.user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        await session.commit()

    await callback.answer(
        "✅ Платёж удалён"
    )
```

The acting user was already rendered to the payments screen earlier in this same block, so the loop here explicitly skips them and only refreshes everyone else's menu screen — using `AnchorService.broadcast` directly would have overwritten the payments screen just rendered for the actor.

- [ ] **Step 5: Route `payment_payer` (the amount prompt) through the anchor**

Replace `handlers/payment.py:564-579`:

Before:
```python
        await callback.message.edit_text(
            f"💳 Плательщик: <b>{payer.first_name}</b>\n\n"
            "💰 Введите сумму платежа:",
            parse_mode="HTML",
        )

        # Сохраняем актуальное сообщение комнаты
        await RoomViewService.save_message(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
        )

        await session.commit()
```

After:
```python
        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=(
                f"💳 Плательщик: <b>{payer.first_name}</b>\n\n"
                "💰 Введите сумму платежа:"
            ),
        )

        await session.commit()
```

(The old `RoomViewService.save_message` call was re-pointing the anchor at whatever message this callback happened to edit — with `AnchorService.render` always editing the already-tracked anchor, that's no longer needed.)

- [ ] **Step 6: Route `payment_amount`'s prompt through the anchor**

Replace `handlers/payment.py:624-644`:

Before:
```python
    async with AsyncSessionLocal() as session:

        await RoomMessageService.send(
            bot=message.bot,
            session=session,
            room_id=room_id,
            chat_id=message.chat.id,
            text=(
                f"💰 Сумма: <b>{amount:.2f} zł</b>\n\n"
                "📝 Введите название расхода.\n\n"
                "Например:\n"
                "Пицца"
            ),
            parse_mode="HTML",
        )

        await session.commit()

    await state.set_state(
        PaymentState.waiting_description
    )
```

After:
```python
    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is not None:
            await AnchorService.render(
                bot=message.bot,
                session=session,
                room_id=room_id,
                user_id=user.id,
                text=(
                    f"💰 Сумма: <b>{amount:.2f} zł</b>\n\n"
                    "📝 Введите название расхода.\n\n"
                    "Например:\n"
                    "Пицца"
                ),
            )

        await session.commit()

    try:
        await message.delete()
    except Exception:
        pass

    await state.set_state(
        PaymentState.waiting_description
    )
```

- [ ] **Step 7: Route `payment_description`'s final screen through the anchor and broadcast**

Replace `handlers/payment.py:828-868` (from `# ФОРМИРУЕМ ФИНАЛЬНОЕ СООБЩЕНИЕ` through the end of the file):

```python
        # --------------------------------
        # ФОРМИРУЕМ ФИНАЛЬНОЕ СООБЩЕНИЕ
        # --------------------------------

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = (
            "✅ <b>Платёж добавлен</b>\n\n"
            + _payments_text(payments, split)
        )

        await AnchorService.render(
            bot=bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        for member in members:

            if member.user_id == current_user.id:
                continue

            menu_text, menu_keyboard = build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member.user_id == room.owner_id),
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member.user_id,
                text=menu_text,
                keyboard=menu_keyboard,
            )

        await session.commit()

    await state.clear()

    try:
        await message.delete()
    except Exception:
        pass
```

- [ ] **Step 8: Remove the now-unused `RoomMessageService`/`RoomViewService` references**

```bash
grep -n "RoomMessageService\|RoomViewService" handlers/payment.py
```
Expected: no output. If any remain, they were missed in a step above — fix them the same way.

- [ ] **Step 9: Run tests and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.payment"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both succeed.

- [ ] **Step 10: Commit**

```bash
git add handlers/payment.py
git commit -m "feat: route payments flow through AnchorService"
```

---

### Task 13: Receipts list/delete screen uses the anchor

**Files:**
- Modify: `handlers/room_receipts.py`
- Test: covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render`, `AnchorService.broadcast` (Task 2/3), `build_menu_screen` (Task 4).

- [ ] **Step 1: Update imports**

Before (`handlers/room_receipts.py:1-17`):
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.session import AsyncSessionLocal

from keyboards.room_receipts_menu import room_receipts_menu

from services.receipt_service import ReceiptService
from services.room_view_service import RoomViewService
from services.room_access_service import RoomAccessService
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository
```

After:
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.session import AsyncSessionLocal

from keyboards.room_receipts_menu import room_receipts_menu

from services.receipt_service import ReceiptService
from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen
from services.room_access_service import RoomAccessService
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository
```

- [ ] **Step 2: Route `room_receipts` through the anchor**

Replace `handlers/room_receipts.py:68-101` (from building `text` through the end of the function):

```python
    text = "📄 <b>Чеки комнаты</b>\n\n"

    if receipts:

        for receipt in receipts:

            amount = (
                f"{receipt.total:.2f} zł"
                if receipt.total is not None
                else "Неизвестно"
            )

            text += (
                f"🧾 Чек #{receipt.id}\n"
                f"💰 {amount}\n\n"
            )

    else:

        text += "Чеков пока нет.\n\n"

    text += (
        "───────────────\n\n"
        f"💰 Общая сумма:\n"
        f"<b>{total:.2f} zł</b>"
    )

    async with AsyncSessionLocal() as session:

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=room_receipts_menu(room_id),
        )

        await session.commit()

    await callback.answer()
```

(`current_user` from the earlier `async with` block is out of scope by the time this runs, since the original code closes its session before building `text` — move the `AnchorService.render` call inside the same `async with AsyncSessionLocal() as session:` block that fetches `receipts`/`total` instead, right after they're fetched, so `current_user` and `session` are both still valid. Concretely: keep everything from `handlers/room_receipts.py:31-66` as-is, but don't let that `async with` block end before rendering — build `text` inside it and call `AnchorService.render` there, then `await session.commit()`, then dedent to `await callback.answer()`.)

- [ ] **Step 3: Route `delete_receipt`'s confirmation prompt through the anchor**

Replace `handlers/room_receipts.py:144-172` (from `builder = InlineKeyboardBuilder()` through the end of the function):

```python
        builder = InlineKeyboardBuilder()

        for receipt in receipts:

            amount = (
                f"{receipt.total:.2f} zł"
                if receipt.total is not None
                else "Неизвестно"
            )

            builder.button(
                text=f"🧾 #{receipt.id} • {amount}",
                callback_data=f"delete_receipt_confirm:{receipt.id}",
            )

        builder.button(
            text="⬅️ Назад",
            callback_data=f"room_receipts:{room_id}",
        )

        builder.adjust(1)

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text="🗑 <b>Выберите чек для удаления</b>",
            keyboard=builder.as_markup(),
        )

        await session.commit()

    await callback.answer()
```

Same adjustment as Step 2: keep this inside the existing `async with AsyncSessionLocal() as session:` block (`handlers/room_receipts.py:112-142`) rather than closing it first.

- [ ] **Step 4: Route `delete_receipt_confirm` through the anchor and broadcast**

Replace `handlers/room_receipts.py:254-278` (from `# ОБНОВЛЯЕМ ОСНОВНОЙ ЭКРАН` through the end of the file):

```python
        # --------------------------------
        # ОБНОВЛЯЕМ ЭКРАНЫ ВСЕХ УЧАСТНИКОВ
        # --------------------------------

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        async def render_menu_for(member_user_id):
            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
            )

        await AnchorService.broadcast(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            render_fn=render_menu_for,
        )

        # --------------------------------
        # ФИКСИРУЕМ ТРАНЗАКЦИЮ
        # --------------------------------

        await session.commit()

    await callback.answer(
        "✅ Чек удален."
    )

    # --------------------------------
    # ВОЗВРАЩАЕМ СПИСОК ЧЕКОВ
    # --------------------------------

    await room_receipts(callback)
```

This broadcasts the menu screen to everyone, including the deleter — matching the "no separate screen for the actor" simplicity of this particular flow (the deleter immediately sees the receipts list again via the trailing `await room_receipts(callback)` call, which re-renders their anchor to the receipts screen right after).

- [ ] **Step 5: Run tests and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.room_receipts"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both succeed.

- [ ] **Step 6: Commit**

```bash
git add handlers/room_receipts.py
git commit -m "feat: route receipts list/delete screens through AnchorService"
```

---

### Task 14: Settlement create/confirm use the anchor, and trigger finalize

**Files:**
- Modify: `handlers/settlement.py`
- Test: covered by Task 16.

**Interfaces:**
- Consumes: `AnchorService.render`, `AnchorService.ping`, `AnchorService.finalize` (Tasks 2/3/6), `build_closed_screen` (Task 5), `SettlementService.is_room_fully_settled(session, room_id, total_debt)` (`services/settlement_service.py`, unchanged, already exists but was never called anywhere).
- Produces: removes the `RoomMessageService.send` calls and the separate settlement-notification message thread entirely.

- [ ] **Step 1: Update imports**

Before (`handlers/settlement.py:1-24`):
```python
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_message_service import RoomMessageService
from services.room_member_service import RoomMemberService
from services.settlement_permission_service import (
    SettlementPermission,
    SettlementPermissionService,
)
from services.settlement_service import SettlementService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService

from keyboards.settlement_menu import settlement_menu

logger = logging.getLogger(__name__)

router = Router()
```

After:
```python
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.settlement_permission_service import (
    SettlementPermission,
    SettlementPermissionService,
)
from services.settlement_service import SettlementService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService
from services.anchor_service import AnchorService, build_closed_screen

logger = logging.getLogger(__name__)

router = Router()
```

`keyboards/settlement_menu.py` is no longer used by this file after this task — if `grep -rn settlement_menu --include="*.py" .` shows no other callers once this task is done, delete it in Step 4.

- [ ] **Step 2: Rewrite `settlement_create`**

Replace `handlers/settlement.py:199-319` (from `# ПРОВЕРЯЕМ СУММУ` through the end of the function):

```python
        # --------------------------------
        # ПРОВЕРЯЕМ СУММУ
        # --------------------------------

        if abs(actual_amount - requested_amount) > 0.01:
            await callback.answer(
                "⚠️ Сумма долга изменилась. "
                "Обновите расчёт.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРЯЕМ, НЕТ ЛИ УЖЕ PENDING
        # --------------------------------

        pending = (
            await SettlementService.get_pending_for_receiver(
                session=session,
                room_id=room_id,
                user_id=to_user_id,
            )
        )

        for item in pending:

            if (
                item.from_user_id == from_user_id
                and abs(
                    float(item.amount) - actual_amount
                ) <= 0.01
            ):
                await callback.answer(
                    "ℹ️ Это погашение уже ожидает "
                    "подтверждения получателя.",
                    show_alert=True,
                )
                return

        # --------------------------------
        # СОЗДАЁМ PENDING SETTLEMENT
        # --------------------------------

        settlement = (
            await SettlementService.create_settlement(
                session=session,
                room_id=room_id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=actual_amount,
            )
        )

        if settlement is None:
            await callback.answer(
                "❌ Не удалось создать погашение.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
        # --------------------------------

        debtor = await UserRepository.get_by_id(
            session=session,
            user_id=from_user_id,
        )

        receiver = await UserRepository.get_by_id(
            session=session,
            user_id=to_user_id,
        )

        debtor_name = (
            debtor.first_name
            if debtor
            else "Пользователь"
        )

        receiver_name = (
            receiver.first_name
            if receiver
            else "Пользователь"
        )

        # --------------------------------
        # ОБНОВЛЯЕМ ЯКОРНЫЕ СООБЩЕНИЯ ОБЕИХ СТОРОН
        # --------------------------------

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        async def render_closed_for(member_user_id):

            pending_for_debtor = (
                await SettlementService.get_pending_for_debtor(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            pending_for_receiver = (
                await SettlementService.get_pending_for_receiver(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            return build_closed_screen(
                room=room,
                members=members,
                transfers=transfers,
                user_id=member_user_id,
                pending_for_debtor=pending_for_debtor,
                pending_for_receiver=pending_for_receiver,
            )

        for member_user_id in (from_user_id, to_user_id):
            text_for_member, keyboard_for_member = await render_closed_for(
                member_user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member_user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        # --------------------------------
        # PUSH-УВЕДОМЛЕНИЕ ПОЛУЧАТЕЛЮ
        # --------------------------------

        if receiver is not None:
            await AnchorService.ping(
                bot=bot,
                chat_id=receiver.telegram_id,
                text=(
                    "🔔 <b>Ожидается погашение</b>\n\n"
                    f"👤 <b>{debtor_name}</b> отметил(а), что "
                    f"оплатил(а) вам <b>{actual_amount:.2f} zł</b>.\n\n"
                    "Откройте комнату, чтобы подтвердить получение."
                ),
            )

        # --------------------------------
        # ФИКСИРУЕМ TRANSACTION
        # --------------------------------

        await session.commit()

    await callback.answer(
        "✅ Ожидается подтверждение получателя."
    )
```

- [ ] **Step 3: Rewrite `settlement_confirm`**

Replace `handlers/settlement.py:400-...` (the whole body of `settlement_confirm`, from `# ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ` through the end of the function — this callback_data no longer needs `room_id` embedded since `settlement.room_id` is already on the fetched row, but keep the existing `_, settlement_id_str, room_id_str = callback.data.split(":")` unpacking as-is for compatibility with `keyboards/closed_room_menu.py`'s existing `settlement_confirm:{settlement.id}` callback — check that keyboard's callback_data shape first):

First, check `keyboards/closed_room_menu.py:69-73` (already read — it's `f"settlement_confirm:{settlement.id}"`, i.e. **no** `room_id` in the callback data, unlike what `handlers/settlement.py`'s current `settlement_confirm` expects (`_, settlement_id_str, room_id_str = callback.data.split(":")`). This mismatch exists in the current code already — the button that's actually reachable from `render_closed`/`closed_room_menu` only ever sends `settlement_confirm:{id}`, so the pre-existing `settlement_confirm` handler's `room_id_str` unpacking would already `ValueError` if it were ever triggered via that button; the only working caller today was the separate notification message's own `settlement_menu(room_id=room_id, settlement_id=settlement.id)` (`keyboards/settlement_menu.py`), which this task removes. Fix the unpacking to match `closed_room_menu`'s actual format and read `room_id` from the settlement row instead:

```python
@router.callback_query(
    F.data.startswith("settlement_confirm:")
)
async def settlement_confirm(
    callback: CallbackQuery,
    bot,
):
    settlement_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        current_user = (
            await UserRepository.get_by_telegram_id(
                session=session,
                telegram_id=callback.from_user.id,
            )
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        settlement = await SettlementService.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

        if settlement is None:
            await callback.answer(
                "❌ Погашение не найдено.",
                show_alert=True,
            )
            return

        room_id = settlement.room_id

        permission = await SettlementPermissionService.can_confirm(
            session=session,
            room_id=room_id,
            settlement_id=settlement_id,
            actor_user_id=current_user.id,
        )

        if permission == SettlementPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.SETTLEMENT_NOT_FOUND:
            await callback.answer(
                "❌ Погашение не найдено.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.WRONG_ROOM:
            await callback.answer(
                "❌ Погашение относится к другой комнате.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.NOT_RECEIVER:
            await callback.answer(
                "❌ Только получатель может "
                "подтвердить погашение.",
                show_alert=True,
            )
            return

        debtor = await UserRepository.get_by_id(
            session=session,
            user_id=settlement.from_user_id,
        )

        confirmed, status = (
            await SettlementService.confirm_settlement(
                session=session,
                settlement_id=settlement_id,
                confirmer_user_id=current_user.id,
            )
        )

        if status == "already_confirmed":
            await callback.answer(
                "ℹ️ Это погашение уже подтверждено.",
                show_alert=True,
            )
            return

        if status == "not_receiver":
            await callback.answer(
                "❌ Только получатель может "
                "подтвердить погашение.",
                show_alert=True,
            )
            return

        if status != "confirmed" or confirmed is None:
            await callback.answer(
                "❌ Не удалось подтвердить погашение.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ОБНОВЛЯЕМ ЯКОРНЫЕ СООБЩЕНИЯ ОБЕИХ СТОРОН
        # --------------------------------

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        async def render_closed_for(member_user_id):

            pending_for_debtor = (
                await SettlementService.get_pending_for_debtor(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            pending_for_receiver = (
                await SettlementService.get_pending_for_receiver(
                    session=session,
                    room_id=room_id,
                    user_id=member_user_id,
                )
            )

            return build_closed_screen(
                room=room,
                members=members,
                transfers=transfers,
                user_id=member_user_id,
                pending_for_debtor=pending_for_debtor,
                pending_for_receiver=pending_for_receiver,
            )

        for member_user_id in (settlement.from_user_id, settlement.to_user_id):
            text_for_member, keyboard_for_member = await render_closed_for(
                member_user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member_user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        # --------------------------------
        # PUSH-УВЕДОМЛЕНИЕ ДОЛЖНИКУ
        # --------------------------------

        if debtor is not None:
            await AnchorService.ping(
                bot=bot,
                chat_id=debtor.telegram_id,
                text=(
                    "✅ <b>Погашение подтверждено</b>\n\n"
                    f"Получатель подтвердил получение "
                    f"<b>{float(settlement.amount):.2f} zł</b>."
                ),
            )

        # --------------------------------
        # ПРОВЕРЯЕМ, ПОЛНОСТЬЮ ЛИ ПОГАШЕНА КОМНАТА
        # --------------------------------

        total_debt = sum(
            float(transfer["amount"])
            for transfer in transfers
        )

        fully_settled = await SettlementService.is_room_fully_settled(
            session=session,
            room_id=room_id,
            total_debt=total_debt,
        )

        if fully_settled and room.status == "closed":
            await AnchorService.finalize(
                bot=bot,
                session=session,
                room_id=room_id,
            )

        await session.commit()

    await callback.answer(
        "✅ Деньги получены."
    )
```

Note: `transfers` here comes from `DebtService.calculate` using `confirmed_settlements` **before** this settlement's confirmation is reflected — since `confirm_settlement` already ran above and `confirmed_settlements` is fetched afterward, it correctly includes the just-confirmed settlement, so `total_debt` reflects the post-confirmation state. `is_room_fully_settled` re-fetches confirmed settlements itself internally (see `services/settlement_service.py:158-174`), so this is consistent.

- [ ] **Step 4: Remove `keyboards/settlement_menu.py` if unused**

```bash
grep -rn "settlement_menu" --include="*.py" .
```
Expected: no matches outside `keyboards/settlement_menu.py` itself. If so:
```bash
git rm keyboards/settlement_menu.py
```

- [ ] **Step 5: Run tests and check imports**

Run:
```bash
.venv/Scripts/python.exe -c "import handlers.settlement"
.venv/Scripts/python.exe -m pytest -v
```
Expected: both succeed.

- [ ] **Step 6: Commit**

```bash
git add handlers/settlement.py
git rm -f keyboards/settlement_menu.py
git commit -m "feat: route settlement create/confirm through AnchorService and trigger finalize"
```

---

### Task 15: Retire `RoomMessage`

**Files:**
- Delete: `services/room_message_service.py`
- Delete: `repositories/room_message_repository.py`
- Modify: `database/models.py` (remove `RoomMessage`)
- Modify: `repositories/room_repository.py` (drop the `RoomMessage` delete + import)
- Create: `alembic/versions/<timestamp>_drop_room_messages.py`

**Interfaces:**
- Consumes: nothing (this is cleanup after Tasks 7-14 removed every call site).
- Produces: nothing new; removes the `RoomMessage` model and table.

- [ ] **Step 1: Confirm no call sites remain**

```bash
grep -rn "RoomMessageService\|RoomMessageRepository\|RoomMessage" --include="*.py" . | grep -v "docs/superpowers"
```
Expected: only `database/models.py` (the class definition) and `repositories/room_repository.py` (the import + delete call). If anything else shows up, a Task 7-14 edit was missed — go fix it before continuing.

- [ ] **Step 2: Delete the service and repository**

```bash
git rm services/room_message_service.py repositories/room_message_repository.py
```

- [ ] **Step 3: Remove `RoomMessage` from `database/models.py`**

Delete `database/models.py:324-345` (the `class RoomMessage(Base): ...` block, from the class definition to the end of the file).

- [ ] **Step 4: Update `repositories/room_repository.py`**

Before (`repositories/room_repository.py:1-13`):
```python
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Room,
    RoomView,
    RoomMessage,
    RoomSettlement,
    RoomPayment,
    RoomHistory,
    Receipt,
    RoomMember,
)
```

After:
```python
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Room,
    RoomView,
    RoomSettlement,
    RoomPayment,
    RoomHistory,
    Receipt,
    RoomMember,
)
```

Delete `repositories/room_repository.py:83-87` (the `await session.execute(delete(RoomMessage)...)` block).

- [ ] **Step 5: Generate the Alembic migration**

Run:
```bash
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "drop room_messages table"
```
Expected: a new file under `alembic/versions/` whose `upgrade()` calls `op.drop_table('room_messages')` and whose `downgrade()` recreates it. Open the generated file and confirm it only touches `room_messages` — if `autogenerate` picked up unrelated diffs, trim the migration to just the `room_messages` drop/recreate.

- [ ] **Step 6: Run tests**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS. `tests/conftest.py::session` uses `Base.metadata.create_all` against an in-memory SQLite DB (not Alembic), so this migration doesn't affect the test DB directly — it only matters for real Postgres/SQLite deployments, which is why Step 5 exists separately from the test run.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: drop RoomMessage — fully replaced by AnchorService/RoomView"
```

---

### Task 16: End-to-end happy-path test

**Files:**
- Create: `tests/test_single_anchor_flow.py`

**Interfaces:**
- Consumes: `AnchorService` (all methods, Tasks 2/3/6), `build_menu_screen`, `build_closed_screen`, `build_settled_screen` (Tasks 4/5), `FakeBot` (Task 1), `tests/helpers.py::create_users_and_room`, and the service layer used throughout (`ReceiptService`, `RoomPaymentService`, `SettlementService`, `DebtService`, `RoomService`) — all unchanged.

This test exercises the service-level flow end to end without going through the aiogram `Router` dispatch machinery (there's no existing precedent in this codebase for driving handlers through aiogram's test client, and building one is out of scope for this feature — see the design spec's "Non-goals"). It proves the same thing the handler wiring in Tasks 7-14 relies on: that a full room lifecycle, driven purely through the services those handlers call, ends with every anchor showing the right thing and the room gone from the DB.

- [ ] **Step 1: Write the test**

```python
import pytest

pytest.importorskip("aiosqlite")

from services.anchor_service import (
    AnchorService,
    build_closed_screen,
    build_menu_screen,
)
from services.debt_service import DebtService
from services.receipt_service import ReceiptService
from services.room_payment_service import RoomPaymentService
from services.room_service import RoomService
from services.settlement_service import SettlementService
from repositories.room_repository import RoomRepository

from .fakes import FakeBot
from .helpers import create_users_and_room


async def test_full_room_lifecycle_stays_on_one_anchor_each(session, tmp_path):
    users, room, members = await create_users_and_room(session, count=2)
    payer, debtor = users
    bot = FakeBot()

    # --------------------------------
    # КАЖДЫЙ УЧАСТНИК ПОЛУЧАЕТ ЯКОРЬ
    # --------------------------------

    for index, user in enumerate(users):
        await AnchorService.create(
            bot=bot,
            session=session,
            room_id=room.id,
            user_id=user.id,
            chat_id=100 + index,
            text="Комната создана",
        )

    await session.commit()

    assert len(bot.sent) == 2

    # --------------------------------
    # ДОБАВЛЯЕМ ЧЕК, ОБНОВЛЯЕМ ОБА ЯКОРЯ
    # --------------------------------

    receipt_path = tmp_path / "receipt.jpg"
    receipt_path.write_bytes(b"fake-image")

    await ReceiptService.save_receipt(
        session=session,
        room_id=room.id,
        photo_path=str(receipt_path),
        total=100.0,
    )

    await session.commit()

    total = await ReceiptService.get_room_total(
        session=session,
        room_id=room.id,
    )

    async def render_menu_for(member_user_id):
        return build_menu_screen(
            room=room,
            total=total,
            members=members,
            is_owner=(member_user_id == room.owner_id),
        )

    await AnchorService.broadcast(
        bot=bot,
        session=session,
        room_id=room.id,
        render_fn=render_menu_for,
    )

    assert len(bot.edited) == 2
    assert all("100.00 zł" in entry["text"] for entry in bot.edited)
    # No new messages were sent for the receipt confirmation — same anchors.
    assert len(bot.sent) == 2

    # --------------------------------
    # ДОБАВЛЯЕМ ПЛАТЁЖ
    # --------------------------------

    await RoomPaymentService.create_payment(
        session=session,
        room_id=room.id,
        user_id=payer.id,
        amount=100.0,
        description="Dinner",
    )

    await session.commit()

    # --------------------------------
    # ЗАКРЫВАЕМ КОМНАТУ
    # --------------------------------

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room.id,
    )

    transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=[],
    )

    assert transfers == [
        {
            "from_user_id": debtor.id,
            "to_user_id": payer.id,
            "amount": 50.0,
        }
    ]

    async def render_closed_for(member_user_id):
        return build_closed_screen(
            room=room,
            members=members,
            transfers=transfers,
            user_id=member_user_id,
            pending_for_debtor=[],
            pending_for_receiver=[],
        )

    await AnchorService.broadcast(
        bot=bot,
        session=session,
        room_id=room.id,
        render_fn=render_closed_for,
    )

    assert len(bot.sent) == 2  # still no new messages

    # --------------------------------
    # ПОГАШАЕМ ДОЛГ
    # --------------------------------

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room.id,
        from_user_id=debtor.id,
        to_user_id=payer.id,
        amount=50.0,
    )

    await session.commit()

    confirmed, status = await SettlementService.confirm_settlement(
        session=session,
        settlement_id=settlement.id,
        confirmer_user_id=payer.id,
    )

    await session.commit()

    assert status == "confirmed"

    confirmed_settlements = await SettlementService.get_confirmed_for_room(
        session=session,
        room_id=room.id,
    )

    final_transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    assert final_transfers == []

    total_debt = sum(
        float(t["amount"]) for t in final_transfers
    )

    fully_settled = await SettlementService.is_room_fully_settled(
        session=session,
        room_id=room.id,
        total_debt=total_debt,
    )

    assert fully_settled is True

    # --------------------------------
    # КОМНАТА УДАЛЯЕТСЯ, СВОДКА ОСТАЁТСЯ
    # --------------------------------

    await AnchorService.finalize(
        bot=bot,
        session=session,
        room_id=room.id,
    )
    await session.commit()

    assert len(bot.sent) == 2       # no new messages, ever
    assert len(bot.edited) == 4     # menu update + settled screen, per user
    for entry in bot.edited[-2:]:
        assert "погашен" in entry["text"].lower()
        assert entry["keyboard"] is None

    assert not receipt_path.exists()

    remaining_room = await RoomRepository.get_by_id(
        session=session,
        room_id=room.id,
    )
    assert remaining_room is None
```

- [ ] **Step 2: Run the test to verify it fails first (sanity check on a clean checkout)**

If you're implementing this plan sequentially, all dependencies already exist by this point, so skip straight to Step 3. If verifying this task in isolation, temporarily stub out `AnchorService.finalize` to confirm the test does fail without it, then restore it.

- [ ] **Step 3: Run the test**

Run: `.venv/Scripts/python.exe -m pytest tests/test_single_anchor_flow.py -v`
Expected: PASS.

- [ ] **Step 4: Run the entire suite one last time**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS, no regressions anywhere.

- [ ] **Step 5: Commit**

```bash
git add tests/test_single_anchor_flow.py
git commit -m "test: add end-to-end single-anchor room lifecycle test"
```

---

## Post-plan manual verification

Automated tests cover the service layer exhaustively; the aiogram handler wiring (Tasks 7-14) is verified by reading, by `python -c "import ..."` import checks, and by the full suite staying green after each task — but not by driving real `Message`/`CallbackQuery` objects through the `Router`. Before calling this feature done, run the bot against a real (or test) Telegram bot token and manually walk the full path once: create a room, send a receipt photo, invite a second account, add a payment from each side, close the room, mark a debt paid, confirm it as received, and confirm the room's final message shows the settled summary and the room can no longer be opened via `/start <code>` (since it's deleted). This is the one part of the feature that must be exercised as a real user, not just asserted against.
