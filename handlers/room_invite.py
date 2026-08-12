from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.qr_service import QRService
from services.room_access_service import RoomAccessService
from services.room_message_service import RoomMessageService

from repositories.user_repository import UserRepository


router = Router()


@router.callback_query(
    F.data.startswith("room_invite:")
)
async def room_invite(
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

        room_code = room.code

    # --------------------------------
    # ГЕНЕРИРУЕМ QR
    # --------------------------------

    qr_path = QRService.generate(
        room_code,
    )

    photo = FSInputFile(
        qr_path,
    )

    # --------------------------------
    # ОТПРАВЛЯЕМ ПРИГЛАШЕНИЕ
    # --------------------------------

    sent_message = await callback.message.answer_photo(
        photo=photo,
        caption=(
            "📤 <b>Приглашение в комнату</b>\n\n"
            f"🔑 Код комнаты:\n"
            f"<code>{room_code}</code>\n\n"
            "Отправьте друзьям QR-код "
            "или сообщите код комнаты."
        ),
        parse_mode="HTML",
    )

    # --------------------------------
    # СОХРАНЯЕМ MESSAGE_ID
    # --------------------------------

    async with AsyncSessionLocal() as session:

        await RoomMessageService.save(
            session=session,
            room_id=room_id,
            chat_id=sent_message.chat.id,
            message_id=sent_message.message_id,
        )

    await callback.answer()