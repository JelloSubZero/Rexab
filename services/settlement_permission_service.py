from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.settlement_service import SettlementService


class SettlementPermission(StrEnum):
    ALLOWED = "allowed"
    NOT_MEMBER = "not_member"
    DEBTOR_NOT_MEMBER = "debtor_not_member"
    RECEIVER_NOT_MEMBER = "receiver_not_member"
    SAME_USER = "same_user"
    SETTLEMENT_NOT_FOUND = "settlement_not_found"
    WRONG_ROOM = "wrong_room"
    NOT_RECEIVER = "not_receiver"


class SettlementPermissionService:

    @staticmethod
    async def can_create(
        session: AsyncSession,
        room_id: int,
        actor_user_id: int,
        from_user_id: int,
        to_user_id: int,
    ) -> SettlementPermission:

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=actor_user_id,
        )

        if not has_access:
            return SettlementPermission.NOT_MEMBER

        debtor_is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=from_user_id,
        )

        if not debtor_is_member:
            return SettlementPermission.DEBTOR_NOT_MEMBER

        receiver_is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=to_user_id,
        )

        if not receiver_is_member:
            return SettlementPermission.RECEIVER_NOT_MEMBER

        if from_user_id == to_user_id:
            return SettlementPermission.SAME_USER

        return SettlementPermission.ALLOWED

    @staticmethod
    async def can_confirm(
        session: AsyncSession,
        room_id: int,
        settlement_id: int,
        actor_user_id: int,
    ) -> SettlementPermission:

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=actor_user_id,
        )

        if not has_access:
            return SettlementPermission.NOT_MEMBER

        settlement = await SettlementService.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

        if settlement is None:
            return SettlementPermission.SETTLEMENT_NOT_FOUND

        if settlement.room_id != room_id:
            return SettlementPermission.WRONG_ROOM

        if settlement.to_user_id != actor_user_id:
            return SettlementPermission.NOT_RECEIVER

        return SettlementPermission.ALLOWED