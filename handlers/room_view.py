from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.room_view_service import RoomViewService

router = Router()


@router.callback_query(F.data.startswith("room_view:"))
async def room_view(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        view = await RoomViewService.render(
            session=session,
            room_id=room_id,
        )

    await callback.message.edit_text(
        view["text"],
        parse_mode="HTML",
        reply_markup=view["reply_markup"],
    )

    await callback.answer()