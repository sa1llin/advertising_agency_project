from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.client_model import Client
from backend.models.order_model import Order
from backend.models.service_model import Service
from backend.models.user_model import User
from backend.schemas.order_schema import OrderCreate, OrderResponse, OrderStatusUpdate, OrderUpdate
from backend.services.order_service import calculate_order_amounts, generate_order_number


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

    manager = db.query(User).filter(User.id == manager_id).first()

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
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    check_client_exists(order_data.client_id, db)
    check_manager_exists(order_data.manager_id, db)
    check_service_exists(order_data.service_id, db)

    calculated_amounts = calculate_order_amounts(
        amount_without_vat=order_data.amount_without_vat,
        vat_rate=order_data.vat_rate,
        discount_rate=order_data.discount_rate,
    )

    new_order = Order(
        order_number="TEMP",
        client_id=order_data.client_id,
        manager_id=order_data.manager_id,
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
    db.commit()
    db.refresh(new_order)

    new_order.order_number = generate_order_number(new_order.id)

    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    order_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    client_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    query = db.query(Order)

    if order_type is not None:
        query = query.filter(Order.order_type == order_type)

    if status_filter is not None:
        query = query.filter(Order.status == status_filter)

    if client_id is not None:
        query = query.filter(Order.client_id == client_id)

    return query.order_by(Order.id.desc()).offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return get_order_or_404(order_id, db)


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order_data: OrderUpdate, db: Session = Depends(get_db)):
    order = get_order_or_404(order_id, db)

    update_data = order_data.model_dump(exclude_unset=True)

    if "client_id" in update_data:
        check_client_exists(update_data["client_id"], db)

    if "manager_id" in update_data:
        check_manager_exists(update_data["manager_id"], db)

    if "service_id" in update_data:
        check_service_exists(update_data["service_id"], db)

    for field_name, field_value in update_data.items():
        setattr(order, field_name, field_value)

    calculated_amounts = calculate_order_amounts(
        amount_without_vat=order.amount_without_vat,
        vat_rate=order.vat_rate,
        discount_rate=order.discount_rate,
    )

    order.discount_amount = calculated_amounts["discount_amount"]
    order.vat_amount = calculated_amounts["vat_amount"]
    order.total_amount = calculated_amounts["total_amount"]

    db.commit()
    db.refresh(order)

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    order = get_order_or_404(order_id, db)

    order.status = status_data.status

    db.commit()
    db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = get_order_or_404(order_id, db)

    db.delete(order)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)