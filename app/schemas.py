from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleEnum(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class EntryTypeEnum(str, Enum):
    income = "income"
    expense = "expense"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    role: RoleEnum | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: RoleEnum
    is_active: bool
    created_at: datetime


class FinancialRecordCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    type: EntryTypeEnum
    category: str = Field(min_length=1, max_length=128)
    entry_date: date
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("category cannot be blank")
        return s


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=14)
    type: EntryTypeEnum | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    entry_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FinancialRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    type: EntryTypeEnum
    category: str
    entry_date: date
    notes: str | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime


class PaginatedRecords(BaseModel):
    items: list[FinancialRecordResponse]
    total: int
    page: int
    page_size: int


class CategoryTotal(BaseModel):
    category: str
    income: Decimal
    expense: Decimal
    net: Decimal


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    by_category: list[CategoryTotal]
    record_count: int


class TrendPoint(BaseModel):
    period_start: date
    income: Decimal
    expense: Decimal
    net: Decimal


class DashboardTrends(BaseModel):
    granularity: str
    points: list[TrendPoint]


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    type: EntryTypeEnum
    category: str
    entry_date: date
    notes: str | None
    created_at: datetime


class ErrorDetail(BaseModel):
    detail: str
    errors: list[dict] | None = None
