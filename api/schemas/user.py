from pydantic import BaseModel, ConfigDict

from database.models import User


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    username: str | None
    first_name: str
    telegram_id: int | None

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls.model_validate(user)
