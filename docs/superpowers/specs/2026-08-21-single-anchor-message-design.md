# Single-anchor-message room flow — design

Date: 2026-08-21
Status: approved, pending implementation plan

## Problem

The bot's room flow (greeting → receipt entry → invite → members → payments →
close → settlement) currently spans a mix of message patterns: some screens
edit a tracked per-user message (`RoomView`), others send brand-new messages
that are never cleaned up except via a bulk best-effort delete on room close
(`RoomMessage` / `RoomMessageService`). Concretely:

- Room creation sends a bare `message.answer(...)`, untracked by `RoomView`.
- Invite sends a **new photo message** (QR code) — can never be folded into
  a text-message edit.
- Receipt upload/confirmation sends a new message per receipt.
- Settlement creation sends **new notification messages** to both parties
  (a second, fully separate notification thread outside the room screen).
- Nothing currently deletes a room once all debts are settled —
  `SettlementService.is_room_fully_settled` exists but is never called.

The owner wants a redesigned flow where each participant has exactly **one**
message per room (created once, edited in place for every step) that
disappears (the room, not necessarily the message) once the room is closed
and fully settled.

## Goals

1. From room creation (or joining via invite link) to the room being fully
   settled, each participant sees **one message per room** that gets edited
   in place for every step: receipt entry, menu, invite, members, payments,
   close confirmation, and the post-close debt breakdown with "I paid" /
   "I received" actions.
2. When the last debt is confirmed settled, the room and all its data are
   deleted from the database (cascade) and receipt files are deleted from
   disk. The chat messages themselves are **not** deleted — each participant's
   anchor message is edited one last time to show the final summary and then
   left alone (no more DB row backs it, so it's simply inert history).
3. Existing business logic (permissions, debt calculation, split logic,
   invite/members/payments feature set) is unchanged — this is a UI/message-
   flow redesign, not a rules change.
4. Settlement actions ("I paid" / "I received") update the same anchor
   message for both parties instead of spawning a separate notification
   thread, but a short, button-less push notification is still sent so the
   counterparty isn't left unaware (Telegram does not push on message edits).

## Non-goals / explicitly out of scope

- The authorization gap found during the earlier code review (any room
  member can currently delete/edit another member's payment or receipt) —
  unrelated to message flow, left as a separate follow-up.
- `NotificationService.notify_member_removed` (member-removal notice) —
  unchanged.
- The OCR pipeline (`services/ocr/*`) — unchanged, only how its result is
  displayed changes.
- `api/` (FastAPI) and `frontend/` — untouched.
- DB-level `ON DELETE CASCADE` — not introduced; this codebase deletes child
  rows explicitly in application code everywhere else, and this feature
  follows that existing convention rather than mixing strategies.

## Architecture

### `services/anchor_service.py` (replaces `services/room_view_service.py`)

The **only** module that calls `bot.send_message` / `bot.edit_message_text` /
`bot.delete_message` for anything room-related. Screen content (text +
keyboard) is still built by the relevant handler/keyboard module; this
service only owns the "how it reaches Telegram, and what message id backs
it" concern — the same responsibility `RoomView`/`RoomViewService` already
have, made exhaustive instead of partial.

Public API:

- `create(bot, session, room_id, user_id, chat_id, text, keyboard=None)`
  Sends the first message for a (room, user) pair and stores it as their
  `RoomView` row. Used at room creation and at invite-link join.

- `render(bot, session, room_id, user_id, text, keyboard=None)`
  Loads the user's `RoomView` row and calls `bot.edit_message_text`. Swallows
  `TelegramBadRequest: message is not modified`. If the edit fails because
  the message is gone (deleted by the user, or bot blocked), falls back to
  `create` and overwrites the stored `RoomView` row so future renders keep
  working. Logs a warning on unexpected failures, never raises.

- `broadcast(bot, session, room_id, render_fn)`
  Loads every `RoomView` row for the room and calls
  `render_fn(room_id, member_user_id) -> (text, keyboard)` then `render`s
  each. Replaces today's duplicated per-member loops in `room_close_confirm`
  and `RoomViewService.refresh_room`.

- `ping(bot, chat_id, text)`
  Fire-and-forget `bot.send_message` with no keyboard, for the settlement
  push notifications. Exceptions are logged and swallowed — matches the
  existing `NotificationService` pattern (never let a best-effort
  notification block or fail the primary flow).

- `finalize(bot, session, room_id)`
  Terminal operation once a room is fully settled. See "Finalize / deletion"
  below.

### Screen builders

Text/keyboard construction stays colocated with the feature it belongs to
(`handlers/room_members.py` builds the members screen, `handlers/payment.py`
builds the payments screen, etc.) rather than centralizing into one
God-service. The one consolidation this design does make: the room-summary
and member-list text builders that are currently duplicated near-verbatim in
three places (`handlers/room.py::room_back`, `RoomViewService.render`,
`handlers/room_members.py`) collapse into shared pure functions in
`services/anchor_service.py` (no I/O, just `(data) -> str`), imported by
whichever handler needs them.

### Invite screen

`handlers/room_invite.py` drops QR generation entirely. The invite becomes a
normal anchor screen: room code, `t.me/{BOT_USERNAME}?start={code}` deep
link, and an inline URL button "📤 Отправить другу" (unchanged share-link
mechanics), plus a back button to the menu. `services/qr_service.py` and
`static/qr/` are deleted; the `qrcode` dependency and `QR_DIR` config entry
are removed once confirmed unused elsewhere.

### Settlement flow rewire

`handlers/settlement.py` currently:
- `settlement_create` sends two **new** messages (to receiver and debtor)
  via `RoomMessageService.send`, each independently tracked for later bulk
  cleanup.
- `settlement_confirm` edits the receiver's separate notification message
  and sends the debtor a further new message.

New behavior:
- `settlement_create`: after creating the pending `RoomSettlement` row, call
  `AnchorService.render` for both the debtor's and receiver's anchors (the
  existing `render_closed` / `closed_room_menu` already compute the correct
  buttons from `pending_for_debtor` / `pending_for_receiver`, so no new
  text-building is needed — just re-render with fresh data). Then
  `AnchorService.ping(receiver.telegram_id, "🔔 ...")`.
- `settlement_confirm`: same re-render of both anchors, plus
  `AnchorService.ping(debtor.telegram_id, "✅ ...")`. Then recompute
  `total_debt` via `DebtService.calculate` and call
  `SettlementService.is_room_fully_settled`; if true, call
  `AnchorService.finalize(bot, session, room_id)`.

This removes the `RoomMessageService.send` calls and roughly 60 lines of
duplicated dual-notification code from `handlers/settlement.py`.

### Room creation / joining

- `handlers/room.py::create_room` calls `AnchorService.create(...)` for the
  "Комната создана, отправьте первый чек" screen — this is the first anchor
  state for the owner.
- `handlers/start.py` (join via `/start <room_code>`) keeps its current
  behavior of landing a new member directly on the menu screen, via
  `AnchorService.create(...)` instead of `RoomViewService.show_room`. As
  today, joining also broadcast-refreshes every other member's anchor
  (member count changed), via `AnchorService.broadcast`.

### Receipt flow

`handlers/receipt.py`:
- On successful photo OCR: instead of `message.answer(...)` (new message) +
  a refresh that only touches *other* members' anchors, broadcast-refresh
  **all** members' anchors (including the sender's) to the menu screen with
  the updated total. The updated total in the menu screen is the
  confirmation — no separate "чек добавлен" banner message. Delete the
  user's photo message afterward (`bot.delete_message`) to keep the chat to
  one message. Stay in `waiting_receipt` state so the next photo continues
  the same anchor.
- Manual total fallback (`manual_total`, used when OCR can't read the
  amount): same pattern — edit the anchor with the prompt and, once
  submitted, with the result; delete the user's text reply after applying
  it.
- `RoomMessageService.save` calls in this file are removed entirely.

### Payments

`handlers/payment.py`: add/edit/delete a payment ends with
`AnchorService.render` (payments screen) instead of ad hoc
`message.answer`/`edit_text`. Any text-based amount/description input from
the user is deleted after being applied, same as the receipt flow.
Permission logic, `SplitBillService`, `DebtService` are untouched — only
where results are displayed changes.

### Close & finalize

- `room_close_confirm`: permission/status checks unchanged. The per-member
  loop with manual `try/except TelegramBadRequest` is replaced by one
  `AnchorService.broadcast(bot, session, room_id, render_closed_screen)`
  call.
- `AnchorService.finalize(bot, session, room_id)`:
  1. Recompute the final per-member summary and edit every anchor to a
     terminal "🎉 Комната закрыта, все расчёты завершены" screen with no
     `reply_markup` (no live buttons remain).
  2. Delete each `Receipt.photo_path` file from disk, best-effort (log and
     continue on missing file / OS error).
  3. Delete DB rows in FK-safe order inside one transaction:
     `room_settlements` → `room_payments` → `room_history` → `receipts` →
     `room_views` → `room_members` → `rooms`.
  4. Single `session.commit()` — either the whole cleanup lands or none of
     it does (aside from the best-effort file deletion, which has no
     transactional meaning).

## Data model changes

- Drop the `RoomMessage` model and `room_messages` table via an Alembic
  migration. Nothing in the new design sends messages that need bulk
  tracked cleanup — invite, receipt, payment, and settlement flows all
  become anchor edits or untracked `ping`s.
- No changes to `Room`, `RoomMember`, `Receipt`, `RoomPayment`,
  `RoomSettlement`, `RoomHistory`, `RoomView`.
- Remove the `qrcode` dependency (if confirmed unused elsewhere in
  `requirements*.txt`) and the `QR_DIR` config entry.

## Error handling

- `AnchorService.render`: `TelegramBadRequest` for "message is not
  modified" is ignored. Any other edit failure (message deleted, chat
  unavailable, bot blocked) falls back to `create`, updating the stored
  `RoomView` row. All failures are logged at warning level; none propagate
  to the caller — matches the existing `refresh_room` behavior, centralized.
- `AnchorService.finalize`: file deletion and per-row DB deletion are each
  best-effort/logged individually where deletion order allows, but the DB
  changes are wrapped in a single transaction — partial cleanup is not
  left half-committed.
- `AnchorService.ping`: exceptions are always swallowed (logged only) — a
  failed push notification must never block or fail the anchor update it
  accompanies.

## Testing

- Existing service-level tests (`debt_service`, `settlement_service`,
  `receipt_service`, `room_payment_service`, all `*_permissions` tests) are
  unaffected — none touch Telegram I/O.
- New unit tests for `AnchorService` (mocked `Bot`):
  - `create` stores a `RoomView` row with the returned message id.
  - `render` edits the message at the stored id.
  - `render` falls back to `create` when the edit fails with a
    "message not found"-style error, and updates the stored row.
  - `broadcast` renders once per `RoomView` row in the room.
  - `finalize` deletes every child row and the room itself, edits every
    anchor to the terminal text, and continues past a failure deleting one
    file or one row.
- One end-to-end-style test (matching the existing `tests/test_room_flow.py`
  / `tests/test_payment_flow.py` pattern, fake `Bot` + real session) walking
  the full happy path: create room → add receipt → invite → add payment →
  close → create settlement → confirm settlement → assert the room and all
  related rows are gone from the DB and the mocked `edit_message_text` calls
  show the expected final text on every participant's anchor.
- Reuse whatever `Bot`/session mocking fixtures already exist in
  `tests/conftest.py` rather than introducing a new fixture style.
