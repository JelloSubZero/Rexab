import logging

from aiogram.exceptions import TelegramBadRequest

from repositories.room_view_repository import RoomViewRepository

logger = logging.getLogger(__name__)

_NOT_MODIFIED = "message is not modified"


class AnchorService:

    @staticmethod
    async def create(
        bot,
        session,
        room_id: int,
        user_id: int,
        chat_id: int,
        text: str,
        keyboard=None,
    ):
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        await RoomViewRepository.save(
            session=session,
            room_id=room_id,
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )

        return message

    @staticmethod
    async def render(
        bot,
        session,
        room_id: int,
        user_id: int,
        text: str,
        keyboard=None,
    ):
        view = await RoomViewRepository.get(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if view is None:
            return

        try:
            await bot.edit_message_text(
                chat_id=view.chat_id,
                message_id=view.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        except TelegramBadRequest as error:

            if _NOT_MODIFIED in error.message:
                return

            logger.warning(
                "Anchor message unreachable for room %s user %s, "
                "recreating",
                room_id,
                user_id,
                exc_info=True,
            )

            await AnchorService.create(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=user_id,
                chat_id=view.chat_id,
                text=text,
                keyboard=keyboard,
            )
