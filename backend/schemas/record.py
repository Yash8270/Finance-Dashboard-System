from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from enum import Enum
from datetime import date, datetime


class TypeEnum(str, Enum):
    income = "income"
    expense = "expense"


# --- Request Schemas ---

class RecordCreate(BaseModel):
    amount: float
    type: TypeEnum
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Category cannot be empty")
        return v


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TypeEnum] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field_required(self):
        """
        Reject empty request bodies.
        At least one field must be provided for an update.
        """
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
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Category cannot be empty or just spaces")
        return v


# --- Response Schema ---

class RecordOut(BaseModel):
    id: int
    user_id: int
    amount: float
    type: TypeEnum
    category: str
    date: date
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
