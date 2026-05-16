from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models.client_model import Client
from backend.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate


router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
):
    new_client = Client(**client_data.model_dump())

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


@router.get("/", response_model=list[ClientResponse])
def get_clients(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Client)

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

    clients = (
        query
        .order_by(Client.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return clients


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    update_data = client_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
):
    try:
        deleted_rows = (
            db.query(Client)
            .filter(Client.id == client_id)
            .delete(synchronize_session=False)
        )

        if deleted_rows == 0:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Клиент не найден",
            )

        db.commit()

        return None

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Клиента нельзя удалить, потому что у него есть связанные заказы",
        )