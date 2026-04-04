from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime


class RoleEnum(str, Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


# --- Request Schemas ---

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)   # bcrypt hard limit is 72 bytes
    role: RoleEnum = RoleEnum.viewer

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        errors = []

        if len(v) < 8:
            errors.append("at least 8 characters")

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
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or just spaces")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


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
