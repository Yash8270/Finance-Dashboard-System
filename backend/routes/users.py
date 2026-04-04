from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models.user import User
from schemas.user import UserOut, UserUpdate
from dependencies.auth import require_admin, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get your own profile",
    description="Returns the profile of the currently authenticated user. Available to all roles.",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Any authenticated user can retrieve their own profile."""
    return current_user


@router.get(
    "",
    response_model=List[UserOut],
    summary="List all users (Admin only)",
)
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).all()


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get a specific user by ID (Admin only)",
)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    summary="Update a user's role, or status (Admin only)",
    description="""
Update one or more user attributes. All fields are optional — send only what you want to change.

**Use cases:**
- Promote a viewer → `{ "role": "analyst" }`
- Deactivate a user → `{ "is_active": false }`
""",
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    return user
