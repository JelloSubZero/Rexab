from datetime import datetime

from pydantic import BaseModel, Field

from database.models import RoomPayment


class PaymentResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    payer_name: str
    amount: float
    description: str | None
    created_at: datetime

    @classmethod
    def from_payment(cls, payment: RoomPayment) -> "PaymentResponse":
        return cls(
            id=payment.id,
            room_id=payment.room_id,
            user_id=payment.user_id,
            payer_name=(
                payment.user.first_name if payment.user else ""
            ),
            amount=payment.amount,
            description=payment.description,
            created_at=payment.created_at,
        )


class PaymentCreateRequest(BaseModel):
    user_id: int = Field(description="Кто заплатил (payer)")
    amount: float = Field(gt=0)
    description: str | None = Field(
        default=None, max_length=255
    )
