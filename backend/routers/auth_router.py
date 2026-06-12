import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_bearer_token, get_current_user
from backend.models.user_model import User
from backend.schemas.user_schema import LoginRequest, LoginResponse, UserResponse
from backend.services.audit_service import log_action
from backend.services.auth_service import create_session, delete_session
from backend.utils.security import hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["Authentication"])


def ensure_initial_admin(db: Session) -> None:
    if db.query(User.id).first() is not None:
        return

    admin = User(
        username=os.getenv("AD_AGENCY_ADMIN_LOGIN", "admin").casefold(),
        password_hash=hash_password(
            os.getenv("AD_AGENCY_ADMIN_PASSWORD", "admin123")
        ),
        role="admin",
        full_name=os.getenv("AD_AGENCY_ADMIN_NAME", "Адміністратор системи"),
        is_active=True,
    )
    try:
        db.add(admin)
        db.commit()
    except IntegrityError:
        db.rollback()


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    ensure_initial_admin(db)
    user = (
        db.query(User)
        .filter(User.username == credentials.username.strip().casefold())
        .first()
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(credentials.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль.",
        )

    token = create_session(user.id)
    log_action(db, user.id, "login", entity_name="user", entity_id=user.id)
    db.commit()
    return LoginResponse(token=token, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log_action(
        db,
        current_user.id,
        "logout",
        entity_name="user",
        entity_id=current_user.id,
    )
    db.commit()
    delete_session(token)
    return None


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
