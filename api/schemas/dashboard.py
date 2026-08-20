from pydantic import BaseModel

from api.schemas.payment import PaymentResponse


class TransferItem(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: float


class DashboardResponse(BaseModel):
    balance: float
    you_owe: float
    you_are_owed: float
    members_count: int
    pending_settlements: int
    recent_payments: list[PaymentResponse]
    transfers: list[TransferItem]
