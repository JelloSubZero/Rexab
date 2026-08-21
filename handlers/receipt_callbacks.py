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

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            await state.clear()
            return

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
