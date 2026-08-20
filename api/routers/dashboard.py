from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.dashboard import DashboardResponse, TransferItem
from api.schemas.payment import PaymentResponse
from database.models import User
from services.debt_service import DebtService
from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.room_payment_service import RoomPaymentService
from services.room_service import RoomService
from services.settlement_service import SettlementService

router = APIRouter(tags=["dashboard"])

RECENT_PAYMENTS_LIMIT = 5


@router.get(
    "/api/rooms/{room_id}/dashboard",
    response_model=DashboardResponse,
)
async def get_dashboard(
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
    payments = await RoomPaymentService.get_room_payments(
        session=session,
        room_id=room_id,
    )
    confirmed_settlements = (
        await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room_id,
        )
    )

    details = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=confirmed_settlements,
    )

    balance = float(
        details["balances"].get(current_user.id, Decimal("0.00"))
    )

    all_settlements = await SettlementService.get_room_history(
        session=session,
        room_id=room_id,
    )

    pending_settlements = sum(
        1
        for settlement in all_settlements
        if settlement.status == "pending"
    )

    recent_payments = sorted(
        payments,
        key=lambda payment: payment.created_at,
        reverse=True,
    )[:RECENT_PAYMENTS_LIMIT]

    return DashboardResponse(
        balance=balance,
        you_owe=-balance if balance < 0 else 0.0,
        you_are_owed=balance if balance > 0 else 0.0,
        members_count=len(members),
        pending_settlements=pending_settlements,
        recent_payments=[
            PaymentResponse.from_payment(payment)
            for payment in recent_payments
        ],
        transfers=[
            TransferItem(
                from_user_id=transfer["from_user_id"],
                to_user_id=transfer["to_user_id"],
                amount=float(transfer["amount"]),
            )
            for transfer in details["transfers"]
        ],
    )
