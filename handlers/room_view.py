from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.room_access_service import RoomAccessService
from services.room_view_service import RoomViewService
from repositories.user_repository import UserRepository


router = Router()


@router.callback_query(
    F.data.startswith("room_view:")
)
async def room_view(
    callback: CallbackQuery,
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

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        view = await RoomViewService.render(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        await callback.message.edit_text(
            view["text"],
            parse_mode="HTML",
            reply_markup=view["reply_markup"],
        )

        # Обновляем актуальный RoomView
        await RoomViewService.save_message(
            session=session,
            room_id=room_id,
            user_id=user.id,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
        )

    await callback.answer()