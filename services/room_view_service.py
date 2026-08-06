from sqlalchemy.ext.asyncio import AsyncSession
from repositories.room_view_repository import RoomViewRepository

from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService
from services.room_service import RoomService
from keyboards.room_menu import room_menu
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

class RoomViewService:

    @staticmethod
    async def build(
        session: AsyncSession,
        room_id: int,
    ):

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

        return {
            "room": room,
            "total": total,
            "members": members,
        }
    @staticmethod
    async def save_message(
        session,
        room_id: int,
        user_id: int,
        chat_id: int,
        message_id: int,
    ):
        return await RoomViewRepository.save(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
        )


    @staticmethod
    async def get_views(
        session,
        room_id: int,
    ):
        return await RoomViewRepository.get_all(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def render(
        session: AsyncSession,
        room_id: int,
    ):

        data = await RoomViewService.build(
            session=session,
            room_id=room_id,
        )

        room = data["room"]
        total = data["total"] or 0
        members = data["members"]

        members_text = ""

        for index, member in enumerate(members, start=1):

            name = (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )

            if member.user_id == room.owner_id:
                name += " 👑"

            members_text += f"{index}. {name}\n"

        if not members_text:
            members_text = "Пока нет участников."

        text = f"""
🏠 <b>Комната</b>

🔑 Код:
<code>{room.code}</code>

💰 Общая сумма:
<b>{total:.2f} zł</b>

👥 Участников: {len(members)}

{members_text}
"""

        return {
            "text": text,
            "reply_markup": room_menu(room.id),
        }

    @staticmethod
    async def refresh_room(
            bot: Bot,
            session: AsyncSession,
            room_id: int,
        ):

            view = await RoomViewService.render(
                session=session,
                room_id=room_id,
            )

            room_views = await RoomViewService.get_views(
                session=session,
                room_id=room_id,
            )

            for room_view in room_views:

                try:

                    await bot.edit_message_text(
                        chat_id=room_view.chat_id,
                        message_id=room_view.message_id,
                        text=view["text"],
                        parse_mode="HTML",
                        reply_markup=view["reply_markup"],
                    )

                except TelegramBadRequest:
                    # Сообщение не изменилось или уже удалено
                    pass

                except Exception as e:
                    print(
                        f"Не удалось обновить комнату: {e}"
                    )

    @staticmethod
    async def show_room(
        bot: Bot,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        room_id: int,
    ):

        view = await RoomViewService.render(
            session=session,
            room_id=room_id,
        )

        msg = await bot.send_message(
            chat_id=chat_id,
            text=view["text"],
            parse_mode="HTML",
            reply_markup=view["reply_markup"],
        )

        await RoomViewService.save_message(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=msg.message_id,
        )

        await RoomViewService.refresh_room(
            bot=bot,
            session=session,
            room_id=room_id,
        )