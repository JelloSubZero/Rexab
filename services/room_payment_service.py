from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_payment_repository import RoomPaymentRepository


class RoomPaymentService:

    @staticmethod
    async def create_payment(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        amount: float,
        description: str | None = None,
    ):
        return await RoomPaymentRepository.create(
            session=session,
            room_id=room_id,
            user_id=user_id,
            amount=amount,
            description=description,
        )

    @staticmethod
    async def get_room_payments(
        session: AsyncSession,
        room_id: int,
    ):
        return await RoomPaymentRepository.get_by_room(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def get_user_payments(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        return await RoomPaymentRepository.get_by_user(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

    @staticmethod
    async def delete_payment(
        session: AsyncSession,
        payment_id: int,
    ):
        return await RoomPaymentRepository.delete(
            session=session,
            payment_id=payment_id,
        )

    @staticmethod
    async def get_payment(
        session: AsyncSession,
        payment_id: int,
    ):
        return await RoomPaymentRepository.get_by_id(
            session=session,
            payment_id=payment_id,
        )