from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.settlement import (
    SettlementCreateRequest,
    SettlementResponse,
)
from database.models import User
from services.debt_service import DebtService
from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.room_payment_service import RoomPaymentService
from services.room_service import RoomService
from services.settlement_permission_service import (
    SettlementPermission,
    SettlementPermissionService,
)
from services.settlement_service import SettlementService

router = APIRouter(tags=["settlements"])


_CREATE_ERRORS = {
    SettlementPermission.NOT_MEMBER: (
        status.HTTP_403_FORBIDDEN,
        "NOT_ROOM_MEMBER",
        "You are not a member of this room.",
    ),
    SettlementPermission.DEBTOR_NOT_MEMBER: (
        status.HTTP_400_BAD_REQUEST,
        "DEBTOR_NOT_MEMBER",
        "The debtor is not a member of this room.",
    ),
    SettlementPermission.RECEIVER_NOT_MEMBER: (
        status.HTTP_400_BAD_REQUEST,
        "RECEIVER_NOT_MEMBER",
        "The receiver is not a member of this room.",
    ),
    SettlementPermission.SAME_USER: (
        status.HTTP_400_BAD_REQUEST,
        "SAME_USER",
        "A settlement cannot be created between the same user.",
    ),
}


@router.get(
    "/api/rooms/{room_id}/settlements",
    response_model=list[SettlementResponse],
)
async def list_settlements(
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

    settlements = await SettlementService.get_room_history(
        session=session,
        room_id=room_id,
    )

    return [
        SettlementResponse.from_settlement(s) for s in settlements
    ]


@router.post(
    "/api/rooms/{room_id}/settlements",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_settlement(
    room_id: int,
    body: SettlementCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    permission = await SettlementPermissionService.can_create(
        session=session,
        room_id=room_id,
        actor_user_id=current_user.id,
        from_user_id=body.from_user_id,
        to_user_id=body.to_user_id,
    )

    if permission != SettlementPermission.ALLOWED:
        status_code, code, message = _CREATE_ERRORS[permission]
        raise ApiError(status_code, code, message)

    # Пересчитываем актуальный долг сами — не доверяем сумме из
    # запроса, ровно как это делает Telegram-бот (защита от
    # устаревших/подделанных данных на клиенте).
    members = await RoomMemberService.get_members(
        session=session, room_id=room_id
    )
    payments = await RoomPaymentService.get_room_payments(
        session=session, room_id=room_id
    )
    confirmed_settlements = (
        await SettlementService.get_confirmed_for_room(
            session=session, room_id=room_id
        )
    )

    transfers = DebtService.calculate(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    actual_amount = next(
        (
            float(transfer["amount"])
            for transfer in transfers
            if transfer["from_user_id"] == body.from_user_id
            and transfer["to_user_id"] == body.to_user_id
        ),
        None,
    )

    if actual_amount is None:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "DEBT_NOT_FOUND",
            "This debt no longer exists.",
        )

    if abs(actual_amount - body.amount) > 0.01:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "AMOUNT_OUT_OF_DATE",
            "The debt amount has changed, refresh and try again.",
        )

    pending = await SettlementService.get_pending_for_receiver(
        session=session,
        room_id=room_id,
        user_id=body.to_user_id,
    )

    already_pending = any(
        item.from_user_id == body.from_user_id
        and abs(float(item.amount) - actual_amount) <= 0.01
        for item in pending
    )

    if already_pending:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "SETTLEMENT_ALREADY_PENDING",
            "This settlement is already waiting for confirmation.",
        )

    settlement = await SettlementService.create_settlement(
        session=session,
        room_id=room_id,
        from_user_id=body.from_user_id,
        to_user_id=body.to_user_id,
        amount=actual_amount,
    )

    if settlement is None:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "SETTLEMENT_CREATE_FAILED",
            "Could not create the settlement.",
        )

    await session.commit()

    return SettlementResponse.from_settlement(settlement)


@router.get(
    "/api/settlements/{settlement_id}",
    response_model=SettlementResponse,
)
async def get_settlement(
    settlement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    settlement = await SettlementService.get_by_id(
        session=session,
        settlement_id=settlement_id,
    )

    if settlement is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "SETTLEMENT_NOT_FOUND",
            "Settlement not found.",
        )

    has_access = await RoomAccessService.check_access(
        session=session,
        room_id=settlement.room_id,
        user_id=current_user.id,
    )

    if not has_access:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )

    return SettlementResponse.from_settlement(settlement)


_CONFIRM_STATUS_ERRORS = {
    "already_confirmed": (
        status.HTTP_409_CONFLICT,
        "ALREADY_CONFIRMED",
        "This settlement is already confirmed.",
    ),
    "not_receiver": (
        status.HTTP_403_FORBIDDEN,
        "NOT_RECEIVER",
        "Only the receiver can confirm this settlement.",
    ),
}


@router.post(
    "/api/settlements/{settlement_id}/confirm",
    response_model=SettlementResponse,
)
async def confirm_settlement(
    settlement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    settlement = await SettlementService.get_by_id(
        session=session,
        settlement_id=settlement_id,
    )

    if settlement is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "SETTLEMENT_NOT_FOUND",
            "Settlement not found.",
        )

    permission = await SettlementPermissionService.can_confirm(
        session=session,
        room_id=settlement.room_id,
        settlement_id=settlement_id,
        actor_user_id=current_user.id,
    )

    if permission == SettlementPermission.NOT_MEMBER:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )

    if permission == SettlementPermission.NOT_RECEIVER:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_RECEIVER",
            "Only the receiver can confirm this settlement.",
        )

    confirmed, confirm_status = (
        await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement_id,
            confirmer_user_id=current_user.id,
        )
    )

    if confirm_status != "confirmed" or confirmed is None:
        status_code, code, message = _CONFIRM_STATUS_ERRORS.get(
            confirm_status,
            (
                status.HTTP_400_BAD_REQUEST,
                "CONFIRM_FAILED",
                "Could not confirm the settlement.",
            ),
        )
        raise ApiError(status_code, code, message)

    await session.commit()

    return SettlementResponse.from_settlement(confirmed)
