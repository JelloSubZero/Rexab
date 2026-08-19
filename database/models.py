from datetime import UTC, datetime
from sqlalchemy import UniqueConstraint

from enum import Enum
from sqlalchemy import Float

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import relationship

from sqlalchemy import BigInteger
from sqlalchemy import DateTime

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(8),
        unique=True,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )

    owner = relationship("User")

class RoomStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id")
    )

    photo_path: Mapped[str] = mapped_column(
        String(255)
    )

    total: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )

    room = relationship("Room")

class RoomMember(Base):
    __tablename__ = "room_members"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_room_member",
        ),
    )

    room = relationship("Room")
    user = relationship("User")


class RoomView(Base):
    __tablename__ = "room_views"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    message_id: Mapped[int] = mapped_column()

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_room_view",
        ),
    )

    room = relationship("Room")
    user = relationship("User")


class RoomPayment(Base):
    __tablename__ = "room_payments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    room = relationship("Room")
    user = relationship("User")


class RoomHistory(Base):
    __tablename__ = "room_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    action: Mapped[str] = mapped_column(
        String(50),
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    room = relationship("Room")
    user = relationship("User")

class RoomSettlement(Base):
    __tablename__ = "room_settlements"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
    )

    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    room = relationship("Room")

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
    )

class RoomMessage(Base):
    __tablename__ = "room_messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    message_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    room = relationship("Room")