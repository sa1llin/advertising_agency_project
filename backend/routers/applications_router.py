from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_admin
from backend.models.application_model import WebsiteApplication
from backend.models.client_model import Client
from backend.models.order_model import Order
from backend.models.user_model import User
from backend.routers.clients_router import find_duplicate_client
from backend.schemas.application_schema import (
    ApplicationCreate,
    ApplicationOrderLink,
    ApplicationResponse,
    ApplicationStatusUpdate,
    ApplicationVisibilityUpdate,
)
from backend.schemas.client_schema import ClientCreate, ClientResponse
from backend.services.audit_service import log_action


router = APIRouter(prefix="/applications", tags=["Website applications"])


def get_application_or_404(application_id: int, db: Session) -> WebsiteApplication:
    application = (
        db.query(WebsiteApplication)
        .filter(WebsiteApplication.id == application_id)
        .first()
    )
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявку не знайдено.",
        )
    return application


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    application_values = application_data.model_dump(exclude={"calculation_data"})
    calculation_data = application_data.calculation_data
    application = WebsiteApplication(
        **application_values,
        calculation_data=(
            calculation_data.model_dump(mode="json")
            if calculation_data is not None
            else None
        ),
    )
    db.add(application)
    db.flush()
    log_action(
        db,
        None,
        "website_application_created",
        entity_name="website_application",
        entity_id=application.id,
        details={
            "service_type": application.service_type,
            "source": application.source,
        },
    )
    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=list[ApplicationResponse])
def get_applications(
    application_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(new|processed|rejected)$",
    ),
    search: str | None = Query(default=None),
    include_hidden: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(WebsiteApplication)
    if application_status:
        query = query.filter(WebsiteApplication.status == application_status)
    if not include_hidden:
        query = query.filter(WebsiteApplication.is_hidden.is_(False))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                WebsiteApplication.full_name.like(pattern),
                WebsiteApplication.phone.like(pattern),
                WebsiteApplication.email.like(pattern),
                WebsiteApplication.comment.like(pattern),
            )
        )
    return (
        query.order_by(WebsiteApplication.submitted_at.desc(), WebsiteApplication.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_application_or_404(application_id, db)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_or_404(application_id, db)
    application.status = status_data.status
    if status_data.status == "new":
        application.processed_by = None
        application.processed_at = None
        application.is_hidden = False
    else:
        application.processed_by = current_user.id
        application.processed_at = datetime.now()

    log_action(
        db,
        current_user.id,
        "website_application_status_updated",
        entity_name="website_application",
        entity_id=application.id,
        details={"status": application.status},
    )
    db.commit()
    db.refresh(application)
    return application


@router.post(
    "/{application_id}/create-client",
    response_model=ClientResponse,
)
def create_client_from_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_or_404(application_id, db)
    if application.client_id is not None:
        client = db.query(Client).filter(Client.id == application.client_id).first()
        if client is not None:
            return client

    client_data = ClientCreate(
        client_type="individual",
        full_name=application.full_name,
        phone=application.phone,
        email=application.email,
        comment=(
            f"Створено із заявки з сайту #{application.id}."
            + (f"\n{application.comment}" if application.comment else "")
        ),
    )
    duplicate = find_duplicate_client(db, client_data.model_dump())
    if duplicate is not None:
        client = duplicate[0]
    else:
        client = Client(**client_data.model_dump())
        db.add(client)
        db.flush()
        log_action(
            db,
            current_user.id,
            "client_created_from_application",
            entity_name="client",
            entity_id=client.id,
            details={"application_id": application.id},
        )

    application.client_id = client.id
    log_action(
        db,
        current_user.id,
        "website_application_linked_to_client",
        entity_name="website_application",
        entity_id=application.id,
        details={"client_id": client.id},
    )
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{application_id}/link-order", response_model=ApplicationResponse)
def link_application_order(
    application_id: int,
    link_data: ApplicationOrderLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_or_404(application_id, db)
    order = db.query(Order).filter(Order.id == link_data.order_id).first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Замовлення не знайдено.",
        )
    if current_user.role != "admin" and order.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Менеджер може прив'язати лише власне замовлення.",
        )
    if application.client_id is not None and order.client_id != application.client_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Клієнт заявки не збігається з клієнтом замовлення.",
        )

    application.client_id = order.client_id
    application.order_id = order.id
    application.status = "processed"
    application.processed_by = current_user.id
    application.processed_at = datetime.now()
    log_action(
        db,
        current_user.id,
        "website_application_converted_to_order",
        entity_name="website_application",
        entity_id=application.id,
        details={"client_id": order.client_id, "order_id": order.id},
    )
    db.commit()
    db.refresh(application)
    return application


@router.patch("/{application_id}/visibility", response_model=ApplicationResponse)
def update_application_visibility(
    application_id: int,
    visibility: ApplicationVisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_or_404(application_id, db)
    if visibility.is_hidden and application.status == "new":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нову заявку спочатку потрібно обробити або відхилити.",
        )
    application.is_hidden = visibility.is_hidden
    log_action(
        db,
        current_user.id,
        "website_application_visibility_updated",
        entity_name="website_application",
        entity_id=application.id,
        details={"is_hidden": application.is_hidden},
    )
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    application = get_application_or_404(application_id, db)
    details = {
        "full_name": application.full_name,
        "client_id": application.client_id,
        "order_id": application.order_id,
    }
    db.delete(application)
    log_action(
        db,
        admin.id,
        "website_application_deleted",
        entity_name="website_application",
        entity_id=application_id,
        details=details,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
