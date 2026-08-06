from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.room_view_service import RoomViewService

from database.session import AsyncSessionLocal

from keyboards.room_receipts_menu import room_receipts_menu

from services.receipt_service import ReceiptService

from services.room_view_service import RoomViewService
from keyboards.room_receipts_menu import room_receipts_menu

router = Router()


@router.callback_query(F.data.startswith("room_receipts:"))
async def room_receipts(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

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

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=room_receipts_menu(room_id),
    )

    await callback.answer()

@router.callback_query(F.data.startswith("delete_receipt:"))
async def delete_receipt(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        receipts = await ReceiptService.get_receipts(
            session=session,
            room_id=room_id,
        )

    from aiogram.utils.keyboard import InlineKeyboardBuilder

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

    await callback.message.edit_text(
        "🗑 <b>Выберите чек для удаления</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("delete_receipt_confirm:"))
async def delete_receipt_confirm(
    callback: CallbackQuery,
):
    receipt_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

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

        await ReceiptService.delete_receipt(
            session=session,
            receipt_id=receipt_id,
        )

        await RoomViewService.refresh_room(
            bot=callback.bot,
            session=session,
            room_id=room_id,
        )

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

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=room_receipts_menu(room_id),
    )

    await callback.answer(
        "✅ Чек удален."
    )