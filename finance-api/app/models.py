import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── Enums ──────────────────────────────────────────────────────────────────────

class Role(str, enum.Enum):
    viewer   = "viewer"    # read-only dashboard access
    analyst  = "analyst"   # read + insights / summary
    admin    = "admin"     # full access including user management


class UserStatus(str, enum.Enum):
    active   = "active"
    inactive = "inactive"


class TransactionType(str, enum.Enum):
    income  = "income"
    expense = "expense"


# ── User ───────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:            Mapped[str]        = mapped_column(String, primary_key=True, default=new_uuid)
    name:          Mapped[str]        = mapped_column(String(100), nullable=False)
    email:         Mapped[str]        = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str]        = mapped_column(String(255), nullable=False)
    role:          Mapped[Role]       = mapped_column(Enum(Role), nullable=False, default=Role.viewer)
    status:        Mapped[UserStatus] = mapped_column(Enum(UserStatus), nullable=False, default=UserStatus.active)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # one-to-many: a user can create many records
    records: Mapped[list["FinancialRecord"]] = relationship("FinancialRecord", back_populates="creator", lazy="select")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


# ── FinancialRecord ────────────────────────────────────────────────────────────

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id:         Mapped[str]             = mapped_column(String, primary_key=True, default=new_uuid)
    amount:     Mapped[float]           = mapped_column(Float, nullable=False)
    type:       Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False, index=True)
    category:   Mapped[str]             = mapped_column(String(50), nullable=False, index=True)
    date:       Mapped[str]             = mapped_column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    notes:      Mapped[str | None]      = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool]            = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[str]             = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    creator: Mapped["User"] = relationship("User", back_populates="records")

    def __repr__(self) -> str:
        return f"<FinancialRecord {self.type} {self.amount} on {self.date}>"
