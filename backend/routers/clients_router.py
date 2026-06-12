from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_admin
from backend.models.client_model import Client
from backend.models.order_model import Order
from backend.models.user_model import User
from backend.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate
from backend.services.audit_service import log_action

router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def normalize_phone(value: object) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def find_duplicate_client(
    db: Session,
    client_data: Mapping[str, object],
    *,
    exclude_client_id: int | None = None,
) -> tuple[Client, str] | None:
    phone = normalize_phone(client_data.get("phone"))
    email = normalize_text(client_data.get("email"))
    tax_number = normalize_text(client_data.get("tax_number"))
    company_name = normalize_text(client_data.get("company_name"))

    query = db.query(Client)
    if exclude_client_id is not None:
        query = query.filter(Client.id != exclude_client_id)

    for client in query.all():
        if phone and normalize_phone(client.phone) == phone:
            return client, "телефоном"
        if email and normalize_text(client.email) == email:
            return client, "email"
        if tax_number and normalize_text(client.tax_number) == tax_number:
            return client, "податковим номером"
        if company_name and normalize_text(client.company_name) == company_name:
            return client, "назвою компанії"

    return None


def raise_duplicate_error(duplicate: tuple[Client, str] | None) -> None:
    if duplicate is None:
        return
    client, matched_by = duplicate
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"Клієнт із таким {matched_by} вже є в базі "
            f"(ID {client.id}: {client.company_name or client.full_name})."
        ),
    )


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_data = client_data.model_dump()
    raise_duplicate_error(find_duplicate_client(db, normalized_data))
    new_client = Client(**normalized_data)

    try:
        db.add(new_client)
        db.flush()
        log_action(
            db,
            current_user.id,
            "client_created",
            entity_name="client",
            entity_id=new_client.id,
        )
        db.commit()
        db.refresh(new_client)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клієнта не вдалося створити через конфлікт даних.",
        ) from error

    return new_client


@router.get("/", response_model=list[ClientResponse])
def get_clients(
    search: str | None = Query(default=None),
    client_type: str | None = Query(
        default=None,
        pattern="^(individual|fop|company)$",
    ),
    is_active: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Client)

    if client_type is not None:
        query = query.filter(Client.client_type == client_type)

    if is_active is not None:
        query = query.filter(Client.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Client.full_name.like(search_pattern),
                Client.company_name.like(search_pattern),
                Client.phone.like(search_pattern),
                Client.email.like(search_pattern),
            )
        )

    return query.order_by(Client.id.desc()).offset(skip).limit(limit).all()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клієнта не знайдено",
        )

    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клієнта не знайдено",
        )

    update_data = client_data.model_dump(exclude_unset=True)
    merged_data = {
        "client_type": client.client_type,
        "full_name": client.full_name,
        "company_name": client.company_name,
        "phone": client.phone,
        "email": client.email,
        "legal_address": client.legal_address,
        "tax_number": client.tax_number,
        "comment": client.comment,
        "is_active": client.is_active,
        **update_data,
    }
    normalized_data = ClientCreate.model_validate(merged_data).model_dump()
    raise_duplicate_error(
        find_duplicate_client(
            db,
            normalized_data,
            exclude_client_id=client_id,
        )
    )

    for field, value in normalized_data.items():
        setattr(client, field, value)

    try:
        log_action(
            db,
            current_user.id,
            "client_updated",
            entity_name="client",
            entity_id=client.id,
            details={"fields": sorted(client_data.model_fields_set)},
        )
        db.commit()
        db.refresh(client)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Дані клієнта конфліктують з наявним записом.",
        ) from error

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клієнта не знайдено",
        )

    has_orders = db.query(Order.id).filter(Order.client_id == client_id).first()
    if has_orders is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Клієнта не можна видалити, оскільки з ним пов'язані замовлення. "
                "Замість видалення деактивуйте запис."
            ),
        )

    try:
        client_name = client.company_name or client.full_name
        db.delete(client)
        log_action(
            db,
            admin.id,
            "client_deleted",
            entity_name="client",
            entity_id=client_id,
            details={"name": client_name},
        )
        db.commit()
        return None
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клієнта не можна видалити через пов'язані дані.",
        ) from error
