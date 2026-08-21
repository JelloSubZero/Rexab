import logging
import os

from aiogram.exceptions import TelegramBadRequest

from repositories.room_view_repository import RoomViewRepository
from keyboards.room_menu import room_menu
from keyboards.room_members_menu import room_members_menu
from keyboards.closed_room_menu import closed_room_menu
from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.room_service import RoomService

logger = logging.getLogger(__name__)

_NOT_MODIFIED = "message is not modified"


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
