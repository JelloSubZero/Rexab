from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.session import AsyncSessionLocal

from keyboards.main_menu import main_menu

from services.user_service import UserService
from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.room_view_service import RoomViewService
from services.notification_service import NotificationService

from repositories.user_repository import UserRepository


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

        # --------------------------------
        # РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
        # --------------------------------

        user = await UserService.register(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

        # --------------------------------
        # ВХОД В КОМНАТУ
        # --------------------------------

        if room_code:

            room = await RoomService.get_by_code(
                session=session,
                code=room_code,
            )

            if room is None:

                await message.answer(
                    "❌ Комната не найдена.",
                    reply_markup=main_menu(),
                )

                return

            # Добавляем пользователя
            member = await RoomMemberService.join_room(
                session=session,
                room_id=room.id,
                user_id=user.id,
            )

            # --------------------------------
            # УВЕДОМЛЕНИЕ О НОВОМ УЧАСТНИКЕ
            # --------------------------------

            if member is not None:

                members = await RoomMemberService.get_members(
                    session=session,
                    room_id=room.id,
                )

                telegram_ids = []

                for room_member in members:

                    # Новому участнику уведомление
                    # не отправляем
                    if room_member.user_id == user.id:
                        continue

                    existing_user = await UserRepository.get_by_id(
                        session=session,
                        user_id=room_member.user_id,
                    )

                    if existing_user:
                        telegram_ids.append(
                            existing_user.telegram_id
                        )

                member_name = (
                    user.first_name
                    or user.username
                    or "Пользователь"
                )

                await NotificationService.notify_member_joined(
                    bot=bot,
                    session=session,
                    room_id=room.id,
                    telegram_ids=telegram_ids,
                    member_name=member_name,
                )

            # --------------------------------
            # ОТКРЫВАЕМ КОМНАТУ
            # --------------------------------

            await RoomViewService.show_room(
                bot=message.bot,
                session=session,
                chat_id=message.chat.id,
                user_id=user.id,
                room_id=room.id,
            )

            return

    # --------------------------------
    # ОБЫЧНЫЙ /START
    # --------------------------------

    await message.answer(
        f"Привет, {message.from_user.first_name}!",
        reply_markup=main_menu(),
    )