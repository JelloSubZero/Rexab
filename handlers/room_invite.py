from urllib.parse import quote

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME
from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.room_access_service import RoomAccessService
from services.anchor_service import AnchorService

from repositories.user_repository import UserRepository


router = Router()


def build_invite_screen(room):

    invite_link = f"https://t.me/{BOT_USERNAME}?start={room.code}"

    share_text = (
        f"Присоединяйся к комнате в Rexab: {invite_link}"
    )

    share_url = (
        "https://t.me/share/url?"
        f"url={quote(invite_link, safe='')}"
        f"&text={quote(share_text, safe='')}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📤 Отправить другу",
        url=share_url,
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room.id}",
    )

    builder.adjust(1)

    text = (
        "📤 <b>Приглашение в комнату</b>\n\n"
        f"🔑 Код комнаты:\n<code>{room.code}</code>\n\n"
        "Отправьте другу ссылку или код."
    )

    return text, builder.as_markup()


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

        text, keyboard = build_invite_screen(room)

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=keyboard,
        )

        await session.commit()

    await callback.answer()