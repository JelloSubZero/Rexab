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