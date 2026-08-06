from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import AsyncSessionLocal
from services.file_service import FileService
from services.receipt_service import ReceiptService
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
        # Получаем данные из FSM
        data = await state.get_data()
        room_id = data.get("room_id")

        if room_id is None:
            await message.answer(
                "❌ Комната не найдена. Создайте новый чек."
            )
            return

        # Сохраняем фотографию
        photo_path = await FileService.save_photo(
            bot=message.bot,
            photo=message.photo[-1],
        )

        # Сохраняем запись в базе данных
        async with AsyncSessionLocal() as session:
            await ReceiptService.save_receipt(
                session=session,
                room_id=room_id,
                photo_path=photo_path,
            )

        # Очищаем состояние
        await state.clear()

        await message.answer(
            "✅ Чек успешно сохранен!\n\n"
            "🔍 Начинаю распознавание..."
        )

    except Exception as e:
        print(f"[Receipt Error] {e}")
        await message.answer(
            "❌ Произошла ошибка при сохранении чека."
        )