import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_message_repository import (
    RoomMessageRepository,
)

logger = logging.getLogger(__name__)


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

            except Exception:
                logger.warning(
                    "Не удалось удалить сообщение %s",
                    message.message_id,
                    exc_info=True,
                )

        await RoomMessageRepository.delete_by_room(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def send(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
        chat_id: int,
        text: str,
        **kwargs,
    ):
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            **kwargs,
        )

        await RoomMessageRepository.create(
            session=session,
            room_id=room_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )

        return message