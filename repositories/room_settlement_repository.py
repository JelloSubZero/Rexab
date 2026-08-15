from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RoomSettlement


class RoomSettlementRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        from_user_id: int,
        to_user_id: int,
        amount: float,
    ):
        settlement = RoomSettlement(
            room_id=room_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=amount,
            status="pending",
        )

        session.add(settlement)

        await session.flush()

        return settlement

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        settlement_id: int,
    ):
        result = await session.execute(
            select(RoomSettlement).where(
                RoomSettlement.id == settlement_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_pending_for_receiver(
        session: AsyncSession,
        room_id: int,
        to_user_id: int,
    ):
        result = await session.execute(
            select(RoomSettlement)
            .where(
                RoomSettlement.room_id == room_id,
                RoomSettlement.to_user_id == to_user_id,
                RoomSettlement.status == "pending",
            )
            .order_by(
                RoomSettlement.created_at.desc()
            )
        )

        return result.scalars().all()

    @staticmethod
    async def get_pending_for_debtor(
        session: AsyncSession,
        room_id: int,
        from_user_id: int,
    ):
        result = await session.execute(
            select(RoomSettlement)
            .where(
                RoomSettlement.room_id == room_id,
                RoomSettlement.from_user_id == from_user_id,
                RoomSettlement.status == "pending",
            )
            .order_by(
                RoomSettlement.created_at.desc()
            )
        )

        return result.scalars().all()

    @staticmethod
    async def get_confirmed_for_room(
        session: AsyncSession,
        room_id: int,
    ):
        result = await session.execute(
            select(RoomSettlement)
            .where(
                RoomSettlement.room_id == room_id,
                RoomSettlement.status == "confirmed",
            )
            .order_by(
                RoomSettlement.confirmed_at.asc()
            )
        )

        return result.scalars().all()

    @staticmethod
    async def confirm(
        session: AsyncSession,
        settlement_id: int,
    ):
        settlement = await RoomSettlementRepository.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

        if settlement is None:
            return None

        if settlement.status != "pending":
            return None

        settlement.status = "confirmed"
        settlement.confirmed_at = datetime.utcnow()

        await session.flush()

        return settlement

    @staticmethod
    async def get_room_history(
        session: AsyncSession,
        room_id: int,
    ):
        result = await session.execute(
            select(RoomSettlement)
            .where(
                RoomSettlement.room_id == room_id,
            )
            .order_by(
                RoomSettlement.created_at.desc()
            )
        )

        return result.scalars().all()