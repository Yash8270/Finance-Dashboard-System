from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from enums import TypeEnum


# --- Request Schemas ---

class RecordCreate(BaseModel):
    # Decimal instead of float — avoids binary floating-point precision loss
    # which is unacceptable in financial applications
    amount: Decimal
    type: TypeEnum
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()

    @field_validator("date")
    @classmethod
    def date_must_not_be_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class RecordUpdate(BaseModel):
    """
    Partial update — send only the fields you want to change.
    At least one field must be provided; an empty body {} returns 422.
    """
    amount: Optional[Decimal] = None
    type: Optional[TypeEnum] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field_required(self):
        """Reject empty request bodies to avoid no-op PATCH calls."""
        provided = {
            field
            for field, value in self.__dict__.items()
            if value is not None
        }
        if not provided:
            raise ValueError(
                "At least one field must be provided to update: "
                "amount, type, category, date, or notes"
            )
        return self

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Category cannot be empty or just spaces")
        return v.strip() if v else v

    @field_validator("date")
    @classmethod
    def date_must_not_be_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


# --- Response Schema ---

class RecordOut(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    type: TypeEnum
    category: str
    date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime  # exposed so clients know when data was last modified

    model_config = {"from_attributes": True}
