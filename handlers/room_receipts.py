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


router = Router()


@router.callback_query(F.data.startswith("room_receipts:"))
async def room_receipts(
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

        receipts = await ReceiptService.get_receipts(
            session=session,
            room_id=room_id,
        )

        total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

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


@router.callback_query(F.data.startswith("delete_receipt:"))
async def delete_receipt(
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

        receipts = await ReceiptService.get_receipts(
            session=session,
            room_id=room_id,
        )

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


@router.callback_query(
    F.data.startswith("delete_receipt_confirm:")
)
async def delete_receipt_confirm(
    callback: CallbackQuery,
):
    receipt_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        # --------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # --------------------------------

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

        # --------------------------------
        # ПОЛУЧАЕМ ЧЕК
        # --------------------------------

        receipt = await ReceiptService.get_receipt(
            session=session,
            receipt_id=receipt_id,
        )

        if receipt is None:
            await callback.answer(
                "❌ Чек не найден.",
                show_alert=True,
            )
            return

        room_id = receipt.room_id

        # --------------------------------
        # ПРОВЕРКА ПРАВ
        # --------------------------------

        permission = await ReceiptPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == ReceiptPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # УДАЛЯЕМ ЧЕК
        # --------------------------------

        deleted = await ReceiptService.delete_receipt(
            session=session,
            receipt_id=receipt_id,
        )

        if not deleted:
            await callback.answer(
                "❌ Не удалось удалить чек.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ОБНОВЛЯЕМ ЭКРАНЫ ВСЕХ УЧАСТНИКОВ
        # --------------------------------

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