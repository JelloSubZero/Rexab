from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.models import RoomStatus

from database.session import AsyncSessionLocal

from keyboards.main_menu import main_menu

from services.user_service import UserService
from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.room_view_service import RoomViewService



router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    bot: Bot,
):
    args = message.text.split(maxsplit=1)

    room_code = (
        args[1]
        if len(args) > 1
        else None
    )

    async with AsyncSessionLocal() as session:

        user = await UserService.register(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

        if room_code:

            room = await RoomService.get_by_code(
                session=session,
                code=room_code,
            )

            if room is None:
                # Пользователя всё равно нужно сохранить.
                await session.commit()

                await message.answer(
                    "❌ Комната не найдена.",
                    reply_markup=main_menu(),
                )
                return

            if room.status != RoomStatus.ACTIVE.value:
                await session.commit()

                await message.answer(
                    "🔒 <b>Комната закрыта</b>\n\n"
                    "Присоединиться к этой комнате больше нельзя.",
                    parse_mode="HTML",
                    reply_markup=main_menu(),
                )
                return

            await RoomMemberService.join_room(
                session=session,
                room_id=room.id,
                user_id=user.id,
            )

            await RoomViewService.show_room(
                bot=message.bot,
                session=session,
                chat_id=message.chat.id,
                user_id=user.id,
                room_id=room.id,
            )

            await session.commit()

            return

        # Обычный /start
        await session.commit()

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу разделить общие расходы: загружай чеки "
        "или добавляй платежи, а я сам посчитаю, кто кому "
        "должен.\n\n"
        "Начни с кнопки ниже 👇",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )