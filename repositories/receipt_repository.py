from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Receipt


class ReceiptRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        photo_path: str,
        total: float | None = None,
    ) -> Receipt:

        receipt = Receipt(
            room_id=room_id,
            photo_path=photo_path,
            total=total,
        )

        session.add(receipt)

        await session.flush()

        return receipt

    @staticmethod
    async def get_room_total(
        session: AsyncSession,
        room_id: int,
    ) -> float:

        result = await session.execute(
            select(Receipt).where(
                Receipt.room_id == room_id
            )
        )

        receipts = result.scalars().all()

        total = 0.0

        for receipt in receipts:
            if receipt.total is not None:
                total += receipt.total

        return total

    @staticmethod
    async def update_total(
        session: AsyncSession,
        receipt_id: int,
        total: float,
    ) -> Receipt | None:

        receipt = await session.get(
            Receipt,
            receipt_id,
        )

        if receipt is None:
            return None

        receipt.total = total

        await session.flush()

        return receipt

    @staticmethod
    async def get_by_room(
        session: AsyncSession,
        room_id: int,
    ) -> list[Receipt]:

        result = await session.execute(
            select(Receipt)
            .where(
                Receipt.room_id == room_id
            )
            .order_by(
                Receipt.id
            )
        )

        return result.scalars().all()

    @staticmethod
    async def delete(
        session: AsyncSession,
        receipt_id: int,
    ) -> bool:

        receipt = await session.get(
            Receipt,
            receipt_id,
        )

        if receipt is None:
            return False

        await session.delete(receipt)
        await session.flush()

        return True

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        receipt_id: int,
    ) -> Receipt | None:

        return await session.get(
            Receipt,
            receipt_id,
        )