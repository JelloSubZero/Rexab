from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import RoomPayment


class RoomPaymentRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        amount: float,
        description: str | None = None,
    ):
        payment = RoomPayment(
            room_id=room_id,
            user_id=user_id,
            amount=amount,
            description=description,
        )

        session.add(payment)

        await session.flush()

        return payment

    @staticmethod
    async def get_by_room(
        session: AsyncSession,
        room_id: int,
    ):
        result = await session.execute(
            select(RoomPayment)
            .options(
                selectinload(RoomPayment.user)
            )
            .where(
                RoomPayment.room_id == room_id,
            )
            .order_by(
                RoomPayment.created_at.asc()
            )
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_user(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        result = await session.execute(
            select(RoomPayment)
            .options(
                selectinload(RoomPayment.user)
            )
            .where(
                RoomPayment.room_id == room_id,
                RoomPayment.user_id == user_id,
            )
        )

        return result.scalars().all()

    @staticmethod
    async def delete(
        session: AsyncSession,
        payment_id: int,
    ):
        payment = await session.get(
            RoomPayment,
            payment_id,
        )

        if payment is None:
            return False

        await session.delete(payment)

        await session.flush()

        return True

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        payment_id: int,
    ):
        result = await session.execute(
            select(RoomPayment)
            .options(
                selectinload(RoomPayment.user)
            )
            .where(
                RoomPayment.id == payment_id
            )
        )

        return result.scalar_one_or_none()