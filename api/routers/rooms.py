from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.room import (
    RoomCreateRequest,
    RoomJoinRequest,
    RoomResponse,
)
from database.models import RoomStatus, User
from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.room_permission_service import RoomPermissionService
from services.room_service import RoomService

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


async def _to_response(
    session: AsyncSession,
    room,
    current_user_id: int,
) -> RoomResponse:

    members = await RoomMemberService.get_members(
        session=session,
        room_id=room.id,
    )

    return RoomResponse.from_room(
        room,
        is_owner=room.owner_id == current_user_id,
        members_count=len(members),
    )


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rooms = await RoomMemberService.get_rooms_for_user(
        session=session,
        user_id=current_user.id,
    )

    return [
        await _to_response(session, room, current_user.id)
        for room in rooms
    ]


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    body: RoomCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    room = await RoomService.create_room(
        session=session,
        owner_id=current_user.id,
    )

    room.name = body.name

    await RoomMemberService.join_room(
        session=session,
        room_id=room.id,
        user_id=current_user.id,
    )

    await session.commit()

    return await _to_response(session, room, current_user.id)


@router.post("/join", response_model=RoomResponse)
async def join_room(
    body: RoomJoinRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    room = await RoomService.get_by_code(
        session=session,
        code=body.code,
    )

    if room is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "ROOM_NOT_FOUND",
            "No room with this invite code.",
        )

    if room.status != RoomStatus.ACTIVE.value:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "ROOM_CLOSED",
            "This room is closed and no longer accepts new members.",
        )

    await RoomMemberService.join_room(
        session=session,
        room_id=room.id,
        user_id=current_user.id,
    )

    await session.commit()

    return await _to_response(session, room, current_user.id)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
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

    return await _to_response(session, room, current_user.id)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
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

    is_owner = await RoomPermissionService.is_owner(
        session=session,
        room_id=room_id,
        user_id=current_user.id,
    )

    if not is_owner:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_OWNER",
            "Only the room owner can delete this room.",
        )

    await RoomService.delete_room(
        session=session,
        room_id=room_id,
    )

    await session.commit()

    return None


@router.post("/{room_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
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

    is_member = await RoomAccessService.check_access(
        session=session,
        room_id=room_id,
        user_id=current_user.id,
    )

    if not is_member:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )

    if room.owner_id == current_user.id:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "OWNER_CANNOT_LEAVE",
            "The room owner cannot leave; delete the room instead.",
        )

    await RoomMemberService.remove_member(
        session=session,
        room_id=room_id,
        user_id=current_user.id,
    )

    await session.commit()

    return None
