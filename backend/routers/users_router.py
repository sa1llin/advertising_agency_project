from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_admin
from backend.models.user_model import User
from backend.schemas.user_schema import (
    ManagerOptionResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.services.audit_service import log_action
from backend.services.auth_service import delete_user_sessions
from backend.utils.security import hash_password


router = APIRouter(prefix="/users", tags=["Users"])


def get_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Працівника не знайдено.",
        )
    return user


@router.get("/managers", response_model=list[ManagerOptionResponse])
def get_managers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(User)
        .filter(User.role == "manager")
        .order_by(User.is_active.desc(), User.full_name, User.id)
        .all()
    )


@router.get("/", response_model=list[UserResponse])
def get_users(
    include_inactive: bool = Query(default=True),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if not include_inactive:
        query = query.filter(User.is_active.is_(True))
    return query.order_by(User.id).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        is_active=user_data.is_active,
    )
    try:
        db.add(user)
        db.flush()
        log_action(
            db,
            admin.id,
            "user_created",
            entity_name="user",
            entity_id=user.id,
            details={"username": user.username, "role": user.role},
        )
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Працівник із таким логіном або email уже існує.",
        ) from error
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = get_user_or_404(user_id, db)
    update_data = user_data.model_dump(exclude_unset=True)

    if user.id == admin.id:
        if update_data.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Не можна деактивувати власний обліковий запис.",
            )
        if update_data.get("role") == "manager":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Не можна забрати роль адміністратора у власного облікового запису.",
            )

    password = update_data.pop("password", None)
    if password:
        user.password_hash = hash_password(password)

    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        log_action(
            db,
            admin.id,
            "user_updated",
            entity_name="user",
            entity_id=user.id,
            details={"fields": sorted(user_data.model_fields_set)},
        )
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Не вдалося оновити працівника через конфлікт даних.",
        ) from error

    if password or user.is_active is False:
        delete_user_sessions(user.id)
    return user
