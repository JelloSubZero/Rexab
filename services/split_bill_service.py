from sqlalchemy.ext.asyncio import AsyncSession

from services.receipt_service import ReceiptService
from services.room_member_service import RoomMemberService


class SplitBillService:

    @staticmethod
    async def calculate(
        session: AsyncSession,
        room_id: int,
    ):

        total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        total = total or 0

        count = len(members)

        if count == 0:

            return {
                "total": total,
                "count": 0,
                "per_person": 0,
                "members": [],
            }

        per_person = round(total / count, 2)

        return {
            "total": total,
            "count": count,
            "per_person": per_person,
            "members": members,
        }