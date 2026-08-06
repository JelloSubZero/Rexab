from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.qr_service import QRService

router = Router()


@router.callback_query(F.data.startswith("room_invite:"))
async def room_invite(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

    if room is None:

        await callback.answer(
            "Комната не найдена.",
            show_alert=True,
        )

        return

    qr_path = QRService.generate(
        room.code,
    )

    photo = FSInputFile(
        qr_path,
    )

    await callback.message.answer_photo(
        photo=photo,
        caption=(
            "📤 <b>Приглашение в комнату</b>\n\n"
            f"🔑 Код комнаты:\n"
            f"<code>{room.code}</code>\n\n"
            "Отправьте друзьям QR-код "
            "или сообщите код комнаты."
        ),
        parse_mode="HTML",
    )

    await callback.answer()