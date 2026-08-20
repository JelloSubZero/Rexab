from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.payment import PaymentCreateRequest, PaymentResponse
from database.models import User
from services.payment_permission_service import (
    PaymentPermission,
    PaymentPermissionService,
)
from services.room_history_service import RoomHistoryService
from services.room_member_service import RoomMemberService
from services.room_payment_service import RoomPaymentService
from services.room_service import RoomService

router = APIRouter(tags=["payments"])


async def _require_room_and_membership(
    session: AsyncSession,
    room_id: int,
    user_id: int,
) -> None:
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

    permission = await PaymentPermissionService.can_manage(
        session=session,
        room_id=room_id,
        user_id=user_id,
    )

    if permission == PaymentPermission.NOT_MEMBER:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )


@router.get(
    "/api/rooms/{room_id}/payments",
    response_model=list[PaymentResponse],
)
async def list_payments(
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _require_room_and_membership(
        session, room_id, current_user.id
    )

    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room_id,
    )

    return [PaymentResponse.from_payment(p) for p in payments]


@router.post(
    "/api/rooms/{room_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    room_id: int,
    body: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _require_room_and_membership(
        session, room_id, current_user.id
    )

    payer_is_member = await RoomMemberService.is_member(
        session=session,
        room_id=room_id,
        user_id=body.user_id,
    )

    if not payer_is_member:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "PAYER_NOT_MEMBER",
            "The payer must be a member of this room.",
        )

    payment = await RoomPaymentService.create_payment(
        session=session,
        room_id=room_id,
        user_id=body.user_id,
        amount=body.amount,
        description=body.description,
    )

    await RoomHistoryService.create(
        session=session,
        room_id=room_id,
        user_id=current_user.id,
        action="payment_added",
        description=body.description,
        amount=body.amount,
    )

    await session.commit()
    await session.refresh(payment, attribute_names=["user"])

    return PaymentResponse.from_payment(payment)


@router.get(
    "/api/payments/{payment_id}",
    response_model=PaymentResponse,
)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payment = await RoomPaymentService.get_payment(
        session=session,
        payment_id=payment_id,
    )

    if payment is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "PAYMENT_NOT_FOUND",
            "Payment not found.",
        )

    permission = await PaymentPermissionService.can_manage(
        session=session,
        room_id=payment.room_id,
        user_id=current_user.id,
    )

    if permission == PaymentPermission.NOT_MEMBER:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "NOT_ROOM_MEMBER",
            "You are not a member of this room.",
        )

    return PaymentResponse.from_payment(payment)
