from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import Role, TransactionType, UserStatus

T = TypeVar("T")


# ── Shared ─────────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    items:       list[T]
    total:       int
    page:        int
    page_size:   int
    total_pages: int


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         "UserResponse"


# ── User ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name:     str   = Field(min_length=2, max_length=100)
    email:    EmailStr
    password: str   = Field(min_length=8, description="At least 8 characters")
    role:     Role  = Role.viewer


class UserUpdate(BaseModel):
    name:   str | None        = Field(default=None, min_length=2, max_length=100)
    role:   Role | None       = None
    status: UserStatus | None = None

    model_config = {"extra": "forbid"}


class UserResponse(BaseModel):
    id:         str
    name:       str
    email:      str
    role:       Role
    status:     UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Financial Record ───────────────────────────────────────────────────────────

class RecordCreate(BaseModel):
    amount:   float           = Field(gt=0, description="Must be positive")
    type:     TransactionType
    category: str             = Field(min_length=1, max_length=50)
    date:     str             = Field(description="YYYY-MM-DD")
    notes:    str | None      = Field(default=None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        import re
        from datetime import date
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Invalid date value")
        return v


class RecordUpdate(BaseModel):
    amount:   float | None           = Field(default=None, gt=0)
    type:     TransactionType | None = None
    category: str | None             = Field(default=None, min_length=1, max_length=50)
    date:     str | None             = None
    notes:    str | None             = Field(default=None, max_length=500)

    model_config = {"extra": "forbid"}

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        if v is None:
            return v
        import re
        from datetime import date
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Invalid date value")
        return v


class RecordResponse(BaseModel):
    id:         str
    amount:     float
    type:       TransactionType
    category:   str
    date:       str
    notes:      str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordFilters(BaseModel):
    type:      TransactionType | None = None
    category:  str | None             = None
    date_from: str | None             = None
    date_to:   str | None             = None
    page:      int                    = Field(default=1, ge=1)
    page_size: int                    = Field(default=20, ge=1, le=100)


# ── Dashboard ──────────────────────────────────────────────────────────────────

class CategoryTotal(BaseModel):
    category: str
    total:    float
    count:    int


class MonthlyTrend(BaseModel):
    month:   str      # YYYY-MM
    income:  float
    expense: float
    net:     float


class DashboardSummary(BaseModel):
    total_income:    float
    total_expenses:  float
    net_balance:     float
    record_count:    int
    category_totals: list[CategoryTotal]
    monthly_trends:  list[MonthlyTrend]
    recent_activity: list[RecordResponse]
