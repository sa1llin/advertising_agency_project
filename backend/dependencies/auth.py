from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user_model import User
from backend.services.auth_service import get_session_user_id


def get_bearer_token(
    authorization: str | None = Header(default=None),
) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.casefold() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необхідна авторизація.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_current_user(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> User:
    user_id = get_session_user_id(token)
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сесію завершено або користувача деактивовано.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ця дія доступна лише адміністратору.",
        )
    return current_user
