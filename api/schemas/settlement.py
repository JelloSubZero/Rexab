from datetime import datetime

from pydantic import BaseModel, Field

from database.models import RoomSettlement


class SettlementResponse(BaseModel):
    id: int
    room_id: int
    from_user_id: int
    to_user_id: int
    amount: float
    status: str
    created_at: datetime
    confirmed_at: datetime | None

    @classmethod
    def from_settlement(
        cls, settlement: RoomSettlement
    ) -> "SettlementResponse":
        return cls(
            id=settlement.id,
            room_id=settlement.room_id,
            from_user_id=settlement.from_user_id,
            to_user_id=settlement.to_user_id,
            amount=float(settlement.amount),
            status=settlement.status,
            created_at=settlement.created_at,
            confirmed_at=settlement.confirmed_at,
        )


class SettlementCreateRequest(BaseModel):
    from_user_id: int = Field(description="Должник")
    to_user_id: int = Field(description="Получатель")
    amount: float = Field(
        gt=0,
        description=(
            "Сумма, которую клиент считает актуальным долгом — "
            "сервер пересчитывает её сам и отклоняет запрос, "
            "если она разошлась с реальным долгом (устаревшие данные)."
        ),
    )
