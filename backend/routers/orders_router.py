from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_admin
from backend.models.client_model import Client
from backend.models.order_model import Order
from backend.models.service_model import Service
from backend.models.user_model import User
from backend.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderUpdate,
)
from backend.schemas.order_schema import OrderProlongRequest
from backend.services.availability_service import validate_space_availability
from backend.services.audit_service import log_action
from backend.services.order_service import (
    calculate_order_amounts,
    generate_order_number,
)
from backend.services.order_pricing_service import build_segment, recalculate_order

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def get_order_or_404(order_id: int, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден",
        )

    return order


def ensure_order_access(
    order: Order,
    current_user: User,
    *,
    allow_unassigned_application: bool = False,
) -> None:
    if current_user.role == "admin" or order.manager_id == current_user.id:
        return
    if (
        allow_unassigned_application
        and order.manager_id is None
        and order.status == "new"
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Менеджер має доступ лише до власних замовлень.",
    )


def check_client_exists(client_id: int, db: Session) -> None:
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )


def check_manager_exists(manager_id: int | None, db: Session) -> None:
    if manager_id is None:
        return

    manager = (
        db.query(User)
        .filter(
            User.id == manager_id,
            User.role == "manager",
            User.is_active.is_(True),
        )
        .first()
    )

    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Менеджер не найден",
        )


def check_service_exists(service_id: int | None, db: Session) -> None:
    if service_id is None:
        return

    service = db.query(Service).filter(Service.id == service_id).first()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена",
        )


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_client_exists(order_data.client_id, db)
    manager_id = (
        current_user.id if current_user.role == "manager" else order_data.manager_id
    )
    check_manager_exists(manager_id, db)
    check_service_exists(order_data.service_id, db)
    validate_space_availability(
        db,
        order_data.order_type,
        order_data.segments,
    )

    calculated_amounts = calculate_order_amounts(
        amount_without_vat=order_data.amount_without_vat,
        vat_rate=order_data.vat_rate,
        discount_rate=order_data.discount_rate,
    )

    new_order = Order(
        order_number="TEMP",
        client_id=order_data.client_id,
        manager_id=manager_id,
        service_id=order_data.service_id,
        order_type=order_data.order_type,
        status=order_data.status,
        rental_start=order_data.rental_start,
        rental_end=order_data.rental_end,
        product_name=order_data.product_name,
        product_size=order_data.product_size,
        material_type=order_data.material_type,
        quantity=order_data.quantity,
        led_seconds=order_data.led_seconds,
        led_block_seconds=order_data.led_block_seconds,
        vat_rate=order_data.vat_rate,
        discount_rate=order_data.discount_rate,
        amount_without_vat=order_data.amount_without_vat,
        discount_amount=calculated_amounts["discount_amount"],
        vat_amount=calculated_amounts["vat_amount"],
        total_amount=calculated_amounts["total_amount"],
        comment=order_data.comment,
    )

    db.add(new_order)
    if order_data.segments:
        for sequence, segment_data in enumerate(order_data.segments, start=1):
            new_order.segments.append(
                build_segment(
                    db,
                    order_data.order_type,
                    segment_data,
                    sequence=sequence,
                    force_kind="initial",
                )
            )
        recalculate_order(new_order)
    db.flush()
    log_action(
        db,
        current_user.id,
        "order_created",
        entity_name="order",
        entity_id=new_order.id,
        details={"manager_id": manager_id},
    )
    db.commit()
    db.refresh(new_order)

    new_order.order_number = generate_order_number(new_order.id)

    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    order_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    client_id: int | None = Query(default=None),
    include_unassigned: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    query = db.query(Order)

    if current_user.role == "manager":
        visibility_filter = Order.manager_id == current_user.id
        if include_unassigned:
            visibility_filter = or_(
                visibility_filter,
                (Order.manager_id.is_(None)) & (Order.status == "new"),
            )
        query = query.filter(visibility_filter)

    if order_type is not None:
        query = query.filter(Order.order_type == order_type)

    if status_filter is not None:
        query = query.filter(Order.status == status_filter)

    if client_id is not None:
        query = query.filter(Order.client_id == client_id)

    return query.order_by(Order.id.desc()).offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)
    ensure_order_access(order, current_user)
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)
    ensure_order_access(order, current_user)

    update_data = order_data.model_dump(exclude_unset=True)
    if current_user.role == "manager" and "manager_id" in update_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Менеджер не може перепризначати замовлення.",
        )

    if "client_id" in update_data:
        check_client_exists(update_data["client_id"], db)

    if "manager_id" in update_data:
        check_manager_exists(update_data["manager_id"], db)

    if "service_id" in update_data:
        check_service_exists(update_data["service_id"], db)

    merged_data = {
        "client_id": order.client_id,
        "manager_id": order.manager_id,
        "service_id": order.service_id,
        "order_type": order.order_type,
        "status": order.status,
        "rental_start": order.rental_start,
        "rental_end": order.rental_end,
        "product_name": order.product_name,
        "product_size": order.product_size,
        "material_type": order.material_type,
        "quantity": order.quantity,
        "led_seconds": order.led_seconds,
        "led_block_seconds": order.led_block_seconds,
        "vat_rate": order.vat_rate,
        "discount_rate": order.discount_rate,
        "amount_without_vat": order.amount_without_vat,
        "comment": order.comment,
        "segments": [
            {
                "segment_kind": segment.segment_kind,
                "advertising_space_id": segment.advertising_space_id,
                "period_start": segment.period_start,
                "period_end": segment.period_end,
                "need_printing": segment.need_printing,
                "video_seconds": segment.video_seconds,
                "impressions_per_day": segment.impressions_per_day,
                "product_type": segment.product_type,
                "product_name": segment.product_name,
                "material_code": segment.material_code,
                "size_code": segment.size_code,
                "color_mode": segment.color_mode,
                "quantity": segment.quantity,
            }
            for segment in order.segments
        ],
        **update_data,
    }
    normalized_model = OrderCreate.model_validate(merged_data)
    normalized_data = normalized_model.model_dump(exclude={"segments"})
    validate_space_availability(
        db,
        normalized_model.order_type,
        normalized_model.segments,
        exclude_order_id=order.id,
    )

    for field_name, field_value in normalized_data.items():
        setattr(order, field_name, field_value)

    if "segments" in update_data:
        order.segments.clear()
        for sequence, segment_data in enumerate(
            normalized_model.segments,
            start=1,
        ):
            order.segments.append(
                build_segment(
                    db,
                    order.order_type,
                    segment_data,
                    sequence=sequence,
                )
            )

    if order.segments:
        recalculate_order(order)
    else:
        calculated_amounts = calculate_order_amounts(
            amount_without_vat=order.amount_without_vat,
            vat_rate=order.vat_rate,
            discount_rate=order.discount_rate,
        )
        order.discount_amount = calculated_amounts["discount_amount"]
        order.vat_amount = calculated_amounts["vat_amount"]
        order.total_amount = calculated_amounts["total_amount"]

    log_action(
        db,
        current_user.id,
        "order_updated",
        entity_name="order",
        entity_id=order.id,
        details={"fields": sorted(order_data.model_fields_set)},
    )
    db.commit()
    db.refresh(order)

    return order


@router.post("/{order_id}/prolong", response_model=OrderResponse)
def prolong_order(
    order_id: int,
    prolong_data: OrderProlongRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)
    ensure_order_access(order, current_user)
    if order.order_type not in ("billboard", "led"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пролонгація доступна лише для білбордів та LED-екранів.",
        )
    validate_space_availability(
        db,
        order.order_type,
        prolong_data.segments,
    )

    next_sequence = (
        max(
            (segment.sequence for segment in order.segments),
            default=0,
        )
        + 1
    )
    for offset, segment_data in enumerate(prolong_data.segments):
        order.segments.append(
            build_segment(
                db,
                order.order_type,
                segment_data,
                sequence=next_sequence + offset,
                force_kind="extension",
            )
        )
    recalculate_order(order)
    log_action(
        db,
        current_user.id,
        "order_prolonged",
        entity_name="order",
        entity_id=order.id,
        details={"segments_added": len(prolong_data.segments)},
    )
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)
    ensure_order_access(
        order,
        current_user,
        allow_unassigned_application=True,
    )

    if order.manager_id is None and current_user.role == "manager":
        if status_data.status != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Спочатку прийміть нову заявку в роботу.",
            )
        order.manager_id = current_user.id

    order.status = status_data.status

    log_action(
        db,
        current_user.id,
        "order_status_updated",
        entity_name="order",
        entity_id=order.id,
        details={"status": status_data.status, "manager_id": order.manager_id},
    )
    db.commit()
    db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)

    db.delete(order)
    log_action(
        db,
        admin.id,
        "order_deleted",
        entity_name="order",
        entity_id=order_id,
        details={"order_number": order.order_number},
    )
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
