from sqlalchemy.ext.asyncio import AsyncSession

from repositories.receipt_repository import ReceiptRepository


class ReceiptService:

    @staticmethod
    async def save_receipt(
        session: AsyncSession,
        room_id: int,
        photo_path: str,
        total: float | None = None,
    ):

        return await ReceiptRepository.create(
            session=session,
            room_id=room_id,
            photo_path=photo_path,
            total=total,
        )

    @staticmethod
    async def update_total(
            session: AsyncSession,
            receipt_id: int,
            total: float,
        ):
            return await ReceiptRepository.update_total(
                session=session,
                receipt_id=receipt_id,
                total=total,
            )

    @staticmethod
    async def get_room_total(
        session: AsyncSession,
        room_id: int,
    ) -> float:

        return await ReceiptRepository.get_room_total(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def get_receipts(
        session,
        room_id: int,
    ):
        return await ReceiptRepository.get_by_room(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def get_receipt(
        session,
        receipt_id: int,
    ):
        return await ReceiptRepository.get_by_id(
            session=session,
            receipt_id=receipt_id,
        )

    @staticmethod
    async def delete_receipt(
        session,
        receipt_id: int,
    ):
        return await ReceiptRepository.delete(
            session=session,
            receipt_id=receipt_id,
        )