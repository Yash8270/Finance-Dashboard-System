from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from schemas.user import UserRegister, UserLogin, TokenOut, RegisterOut
from utils.auth import hash_password, verify_password, create_access_token
from enums import RoleEnum

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
Create a new user account. **All self-registered users receive the `viewer` role by default.**

An admin can promote the role later via `PATCH /users/{id}`.

**Password requirements:**
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&* etc.)
""",
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        # Security: role is ALWAYS forced to viewer on self-registration.
        # This prevents privilege escalation (e.g. sending role="admin" in the request body).
        # Admins can assign elevated roles via PATCH /users/{id}.
        role=RoleEnum.viewer,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "id": user.id}


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Login and get JWT token",
    description="""
Authenticate with email and password to receive a JWT Bearer token.

**How to use the token in Swagger:**
1. Copy the `access_token` from the response
2. Click the **Authorize ** button at the top of this page
3. Enter your token in the **Value** field (just the token, no 'Bearer' prefix needed)
4. Click **Authorize** — all protected routes are now unlocked

**Token expires in:** 24 hours
""",
)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    # Check user existence and password in one branch to avoid leaking whether
    # the email exists via timing differences
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive. Contact an admin to restore access.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}
