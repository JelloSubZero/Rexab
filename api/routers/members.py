from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.member import MemberResponse
from database.models import User
from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.room_permission_service import (
    RemoveMemberPermission,
    RoomPermissionService,
)
from services.room_service import RoomService

router = APIRouter(prefix="/api/rooms/{room_id}/members", tags=["members"])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    room = await RoomService.get_by_id(
        session=session,
        room_id=room_id,
    )

    if room is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "ROOM_NOT_FOUND",
            "Room not found.",
        )

    has_access = await RoomAccessService.check_access(
        session=session,
        room_id=room_id,
        user_id=current_user.id,
    )

    if not has_access:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )

    members = await RoomMemberService.get_members(
        session=session,
        room_id=room_id,
    )

    return [
        MemberResponse.from_member(member, room.owner_id)
        for member in members
    ]


_REMOVE_MEMBER_ERRORS = {
    RemoveMemberPermission.ROOM_NOT_FOUND: (
        status.HTTP_404_NOT_FOUND,
        "ROOM_NOT_FOUND",
        "Room not found.",
    ),
    RemoveMemberPermission.NOT_OWNER: (
        status.HTTP_403_FORBIDDEN,
        "NOT_ROOM_OWNER",
        "Only the room owner can remove members.",
    ),
    RemoveMemberPermission.OWNER_CANNOT_BE_REMOVED: (
        status.HTTP_409_CONFLICT,
        "OWNER_CANNOT_BE_REMOVED",
        "The room owner cannot be removed.",
    ),
}


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    room_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    permission = await RoomPermissionService.can_remove_member(
        session=session,
        room_id=room_id,
        actor_user_id=current_user.id,
        target_user_id=user_id,
    )

    if permission != RemoveMemberPermission.ALLOWED:
        status_code, code, message = _REMOVE_MEMBER_ERRORS[permission]
        raise ApiError(status_code, code, message)

    removed = await RoomMemberService.remove_member(
        session=session,
        room_id=room_id,
        user_id=user_id,
    )

    if not removed:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "MEMBER_NOT_FOUND",
            "This user is not a member of the room.",
        )

    await session.commit()

    return None
