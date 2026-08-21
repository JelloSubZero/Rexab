import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NotificationService:

    # ============================================================
    # НОВЫЙ РАСХОД
    # ============================================================

    @staticmethod
    async def notify_payment_added(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
        telegram_ids: list[int],
        payer_name: str,
        description: str,
        amount: float,
    ):
        """
        Уведомляет участников комнаты
        о добавлении нового платежа.
        """

        text = (
            "💳 <b>Новый расход</b>\n\n"
            f"👤 {payer_name} добавил расход:\n"
            f"📝 {description}\n"
            f"💰 <b>{amount:.2f} zł</b>"
        )

        for telegram_id in telegram_ids:

            try:

                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception:
                logger.warning(
                    "Не удалось отправить уведомление о новом "
                    "расходе пользователю %s",
                    telegram_id,
                    exc_info=True,
                )

    # ============================================================
    # РАСХОД УДАЛЁН
    # ============================================================

    @staticmethod
    async def notify_payment_deleted(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
        telegram_ids: list[int],
        user_name: str,
        description: str,
        amount: float,
    ):
        """
        Уведомляет участников комнаты
        об удалении платежа.
        """

        text = (
            "🗑 <b>Расход удалён</b>\n\n"
            f"👤 {user_name} удалил расход:\n"
            f"📝 {description}\n"
            f"💰 <b>{amount:.2f} zł</b>"
        )

        for telegram_id in telegram_ids:

            try:

                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception:
                logger.warning(
                    "Не удалось отправить уведомление об удалении "
                    "расхода пользователю %s",
                    telegram_id,
                    exc_info=True,
                )

    # ============================================================
    # НОВЫЙ УЧАСТНИК
    # ============================================================

    @staticmethod
    async def notify_member_joined(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
        telegram_ids: list[int],
        member_name: str,
    ):
        """
        Уведомляет участников комнаты
        о присоединении нового пользователя.
        """

        text = (
            "👋 <b>Новый участник</b>\n\n"
            f"👤 <b>{member_name}</b> "
            "присоединился к комнате."
        )

        for telegram_id in telegram_ids:

            try:

                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception:
                logger.warning(
                    "Не удалось отправить уведомление о новом "
                    "участнике пользователю %s",
                    telegram_id,
                    exc_info=True,
                )

    # ============================================================
    # УЧАСТНИК УДАЛЁН
    # ============================================================

    @staticmethod
    async def notify_member_removed(
        bot: Bot,
        session: AsyncSession,
        room_id: int,
        telegram_ids: list[int],
        member_name: str,
    ):
        """
        Уведомляет участников комнаты
        о выходе пользователя.
        """

        text = (
            "👋 <b>Участник вышел</b>\n\n"
            f"👤 <b>{member_name}</b> "
            "покинул комнату."
        )

        for telegram_id in telegram_ids:

            try:

                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception:
                logger.warning(
                    "Не удалось отправить уведомление об удалении "
                    "участника пользователю %s",
                    telegram_id,
                    exc_info=True,
                )

