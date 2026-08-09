from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_settlement_repository import (
    RoomSettlementRepository,
)


class SettlementService:

    @staticmethod
    async def create_settlement(
        session: AsyncSession,
        room_id: int,
        from_user_id: int,
        to_user_id: int,
        amount: float,
    ):
        """
        Создаёт ожидающее погашение.

        from_user_id — должник.
        to_user_id — получатель денег.
        """

        if from_user_id == to_user_id:
            return None

        amount_decimal = Decimal(str(amount))

        if amount_decimal <= 0:
            return None

        return await RoomSettlementRepository.create(
            session=session,
            room_id=room_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=float(amount_decimal),
        )

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        settlement_id: int,
    ):
        return await RoomSettlementRepository.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

    @staticmethod
    async def get_pending_for_receiver(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        """
        Получает погашения, которые ожидают
        подтверждения конкретного получателя.
        """

        return await RoomSettlementRepository.get_pending_for_receiver(
            session=session,
            room_id=room_id,
            to_user_id=user_id,
        )

    @staticmethod
    async def get_pending_for_debtor(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        """
        Получает погашения конкретного должника,
        которые ещё не подтверждены.
        """

        return await RoomSettlementRepository.get_pending_for_debtor(
            session=session,
            room_id=room_id,
            from_user_id=user_id,
        )

    @staticmethod
    async def get_confirmed_for_room(
        session: AsyncSession,
        room_id: int,
    ):
        """
        Получает все подтверждённые погашения комнаты.
        """

        return await RoomSettlementRepository.get_confirmed_for_room(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def confirm_settlement(
        session: AsyncSession,
        settlement_id: int,
        confirmer_user_id: int,
    ):
        """
        Подтверждает погашение.

        Подтвердить может ТОЛЬКО получатель денег:
        settlement.to_user_id == confirmer_user_id
        """

        settlement = await RoomSettlementRepository.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

        if settlement is None:
            return None, "not_found"

        if settlement.status != "pending":
            return None, "already_confirmed"

        if settlement.to_user_id != confirmer_user_id:
            return None, "not_receiver"

        confirmed = await RoomSettlementRepository.confirm(
            session=session,
            settlement_id=settlement_id,
        )

        if confirmed is None:
            return None, "confirm_failed"

        return confirmed, "confirmed"


    @staticmethod
    async def get_room_history(
        session: AsyncSession,
        room_id: int,
    ):
        """
        Получает всю историю погашений комнаты.

        Включает:
        - pending
        - confirmed
        """

        return await RoomSettlementRepository.get_room_history(
            session=session,
            room_id=room_id,
        )
   