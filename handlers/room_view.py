from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.room_access_service import RoomAccessService
from services.room_service import RoomService
from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen
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

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

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

    await callback.answer()
