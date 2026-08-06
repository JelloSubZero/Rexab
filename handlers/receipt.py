from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.room_view_service import RoomViewService

from keyboards.receipt_menu import receipt_menu

from config import RECEIPTS_DIR

from database.session import AsyncSessionLocal

from services.receipt_service import ReceiptService
from services.ocr.ocr_service import OCRService

from states.receipt_state import ReceiptState

router = Router()


@router.message(
    ReceiptState.waiting_receipt,
    F.photo,
)
async def receipt_handler(
    message: Message,
    state: FSMContext,
):
    try:
        data = await state.get_data()

        room_id = data.get("room_id")

        if room_id is None:
            await message.answer("❌ Комната не найдена.")
            return

        photo = message.photo[-1]

        file = await message.bot.get_file(photo.file_id)

        file_name = f"{photo.file_unique_id}.jpg"

        destination = RECEIPTS_DIR / file_name

        await message.bot.download_file(
            file.file_path,
            destination=destination,
        )

        # OCR
        ocr = OCRService()
        result = ocr.process(str(destination))

        async with AsyncSessionLocal() as session:

            receipt = await ReceiptService.save_receipt(
                session=session,
                room_id=room_id,
                photo_path=str(destination),
                total=result.receipt.total,
            )

        # Если сумму определить не удалось
        if result.receipt.total is None:

            await state.update_data(
                receipt_id=receipt.id,
                room_id=room_id,
            )

            await state.set_state(
                ReceiptState.waiting_total,
            )

            await message.answer(
                "❌ Не удалось определить сумму чека.\n\n"
                "Введите общую сумму вручную.\n\n"
                "Например:\n"
                "<code>123.45</code>",
                parse_mode="HTML",
            )

            return

        async with AsyncSessionLocal() as session:

            room_total = await ReceiptService.get_room_total(
                session=session,
                room_id=room_id,
            )

            await RoomViewService.refresh_room(
                bot=message.bot,
                session=session,
                room_id=room_id,
            )

        await state.set_state(
    ReceiptState.waiting_receipt,
)

        await message.answer(
    f"✅ Чек добавлен.\n\n"
    f"🧾 Сумма этого чека: <b>{result.receipt.total:.2f} zł</b>\n"
    f"💰 Общая сумма комнаты: <b>{room_total:.2f} zł</b>",
    parse_mode="HTML",
    reply_markup=receipt_menu(room_id),
)

    except Exception as e:
        print(e)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(
    ReceiptState.waiting_total,
    F.text,
)
async def manual_total(
    message: Message,
    state: FSMContext,
):
    try:
        total = float(
            message.text.replace(",", ".")
        )

    except ValueError:

        await message.answer(
            "❌ Неверный формат.\n\n"
            "Введите сумму, например:\n"
            "<code>123.45</code>",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()

    receipt_id = data.get("receipt_id")

    if receipt_id is None:
        await message.answer("❌ Чек не найден.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:

        receipt = await ReceiptService.update_total(
            session=session,
            receipt_id=receipt_id,
            total=total,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=receipt.room_id,
        )

        await RoomViewService.refresh_room(
            bot=message.bot,
            session=session,
            room_id=receipt.room_id,
        )

    await state.update_data(
    room_id=receipt.room_id,
    )

    await state.set_state(
        ReceiptState.waiting_receipt,
    )


    await message.answer(
    f"✅ Сумма сохранена.\n\n"
    f"🧾 Сумма этого чека: <b>{total:.2f} zł</b>\n"
    f"💰 Общая сумма комнаты: <b>{room_total:.2f} zł</b>",
    parse_mode="HTML",
    reply_markup=receipt_menu(receipt.room_id),
)