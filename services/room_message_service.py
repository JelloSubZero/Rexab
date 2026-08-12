from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_message_repository import (
    RoomMessageRepository,
)


class RoomMessageService:

    @staticmethod
    async def save(
        session: AsyncSession,
        room_id: int,
        chat_id: int,
        message_id: int,
    ):

        return await RoomMessageRepository.create(
            session=session,
            room_id=room_id,
            chat_id=chat_id,
            message_id=message_id,
        )

    @staticmethod
    async def delete_all(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
    ):

        messages = await RoomMessageRepository.get_by_room(
            session=session,
            room_id=room_id,
        )

        for message in messages:

            try:

                await bot.delete_message(
                    chat_id=message.chat_id,
                    message_id=message.message_id,
                )

            except Exception as e:

                print(
                    f"Не удалось удалить сообщение "
                    f"{message.message_id}: {e}"
                )

        await RoomMessageRepository.delete_by_room(
            session=session,
            room_id=room_id,
        )

        await session.commit()