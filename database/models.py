from datetime import datetime

from uuid import uuid4
from enum import Enum
from sqlalchemy import Float

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import relationship

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.session import Base
from pathlib import Path


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
        default=datetime.utcnow,
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
        default=datetime.utcnow
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
        default=datetime.utcnow
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
        default=datetime.utcnow,
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

    room = relationship("Room")
    user = relationship("User")