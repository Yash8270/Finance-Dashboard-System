from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from enums import RoleEnum


# --- Request Schemas ---

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    # bcrypt hard limit is 72 bytes; Field(min_length=8) already enforces the length rule
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce complexity beyond just length.
        Field(min_length=8) handles the 8-char check, so we only check the rest here.
        """
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter (A-Z)")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter (a-z)")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit (0-9)")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v):
            errors.append("at least one special character (!@#$%^&* etc.)")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or just spaces")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """
    Admin-only update schema. All fields are optional — send only what you want to change.
    Allows updating name, role, and/or active status.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field_required(self):
        provided = {f for f, v in self.__dict__.items() if v is not None}
        if not provided:
            raise ValueError(
                "At least one field must be provided: name, role, or is_active"
            )
        return self

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or just spaces")
        return v.strip() if v else v


# --- Response Schemas ---

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterOut(BaseModel):
    """Typed response for POST /auth/register — replaces the untyped dict."""
    message: str
    id: int
