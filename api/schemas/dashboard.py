from pydantic import BaseModel

from api.schemas.payment import PaymentResponse


class DashboardResponse(BaseModel):
    balance: float
    you_owe: float
    you_are_owed: float
    members_count: int
    pending_settlements: int
    recent_payments: list[PaymentResponse]
