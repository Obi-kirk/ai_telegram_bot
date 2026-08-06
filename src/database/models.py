from datetime import datetime
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class Role(str, Enum):
    USER = "user"
    EMPLOYEE = "employee"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(128), default="data")
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default=Role.USER.value)
    status: Mapped[str] = mapped_column(String(16), default=UserStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
