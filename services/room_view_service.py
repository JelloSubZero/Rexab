import logging

from sqlalchemy.ext.asyncio import AsyncSession
from repositories.room_view_repository import RoomViewRepository

from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.room_service import RoomService
from keyboards.room_menu import room_menu
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from keyboards.closed_room_menu import closed_room_menu
from services.debt_service import DebtService
from services.settlement_service import SettlementService
from services.room_payment_service import RoomPaymentService

logger = logging.getLogger(__name__)


class RoomViewService:

    @staticmethod
    async def build(
        session: AsyncSession,
        room_id: int,
    ):

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

        return {
            "room": room,
            "total": total,
            "members": members,
        }
    @staticmethod
    async def save_message(
        session,
        room_id: int,
        user_id: int,
        chat_id: int,
        message_id: int,
    ):
        return await RoomViewRepository.save(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
        )


    @staticmethod
    async def get_views(
        session,
        room_id: int,
    ):
        return await RoomViewRepository.get_all(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def render(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):

        data = await RoomViewService.build(
            session=session,
            room_id=room_id,
        )

        room = data["room"]
        is_owner = room.owner_id == user_id
        total = data["total"] or 0
        members = data["members"]

        members_text = ""

        for index, member in enumerate(members, start=1):

            name = (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )

            if member.user_id == room.owner_id:
                name += " 👑"

            members_text += f"{index}. {name}\n"

        if not members_text:
            members_text = "Пока нет участников."

        room_title = room.name or "Комната"

        text = f"""
🏠 <b>{room_title}</b>

🔑 Код:
<code>{room.code}</code>

💰 Общая сумма:
<b>{total:.2f} zł</b>

👥 Участников: {len(members)}

{members_text}
"""

        return {
            "text": text,
            "reply_markup": room_menu(
            room.id,
            is_owner=is_owner,
        ),
        }



    @staticmethod
    async def render_closed(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            return None

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

        # Актуальные долги после подтвержденных погашений
        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        # Только долги, которые относятся к текущему пользователю
        user_transfers = [
            transfer
            for transfer in transfers
            if (
                transfer["from_user_id"] == user_id
                or transfer["to_user_id"] == user_id
            )
        ]

        # Общая сумма всех непогашенных долгов
        total_debt = sum(
            float(transfer["amount"])
            for transfer in transfers
        )

        debts_text = ""

        for transfer in user_transfers:

            from_member = next(
                (
                    member
                    for member in members
                    if member.user_id
                    == transfer["from_user_id"]
                ),
                None,
            )

            to_member = next(
                (
                    member
                    for member in members
                    if member.user_id
                    == transfer["to_user_id"]
                ),
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
                f"• <b>{from_name}</b> → "
                f"<b>{to_name}</b>: "
                f"<b>{float(transfer['amount']):.2f} zł</b>\n"
            )

        if not debts_text:
            debts_text = (
                "🎉 У вас нет непогашенных долгов."
            )

        # Ожидаемые погашения текущего пользователя
        pending_for_debtor = (
            await SettlementService.get_pending_for_debtor(
                session=session,
                room_id=room_id,
                user_id=user_id,
            )
        )

        pending_for_receiver = (
            await SettlementService.get_pending_for_receiver(
                session=session,
                room_id=room_id,
                user_id=user_id,
            )
        )

        text = (
            "🔒 <b>Комната закрыта</b>\n\n"
            f"💰 Непогашено: "
            f"<b>{total_debt:.2f} zł</b>\n"
            f"👥 Участников: <b>{len(members)}</b>\n\n"
            "👤 <b>Ваши долги</b>\n\n"
            f"{debts_text}"
        )

        return {
            "text": text,
            "reply_markup": closed_room_menu(
                room_id=room_id,
                transfers=user_transfers,
                current_user_id=user_id,
                pending_for_debtor=pending_for_debtor,
                pending_for_receiver=pending_for_receiver,
            ),
        }

    @staticmethod
    async def refresh_room(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
    ):

        room_views = await RoomViewService.get_views(
            session=session,
            room_id=room_id,
        )

        for room_view in room_views:

            view = await RoomViewService.render(
                session=session,
                room_id=room_id,
                user_id=room_view.user_id,
            )

            try:

                await bot.edit_message_text(
                    chat_id=room_view.chat_id,
                    message_id=room_view.message_id,
                    text=view["text"],
                    parse_mode="HTML",
                    reply_markup=view["reply_markup"],
                )

            except TelegramBadRequest:
                pass

            except Exception:
                logger.warning(
                    "Не удалось обновить комнату",
                    exc_info=True,
                )

    @staticmethod
    async def show_room(
        bot: Bot,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        room_id: int,
    ):

        view = await RoomViewService.render(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        msg = await bot.send_message(
            chat_id=chat_id,
            text=view["text"],
            parse_mode="HTML",
            reply_markup=view["reply_markup"],
        )

        await RoomViewService.save_message(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=msg.message_id,
        )

        await RoomViewService.refresh_room(
            bot=bot,
            session=session,
            room_id=room_id,
        )