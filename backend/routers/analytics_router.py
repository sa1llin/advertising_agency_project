from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.client_model import Client
from backend.models.order_model import Order
from backend.models.user_model import User


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders_query = db.query(Order)
    if current_user.role == "manager":
        orders_query = orders_query.filter(Order.manager_id == current_user.id)

    total_revenue = (
        orders_query.with_entities(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.status != "cancelled")
        .scalar()
    )
    status_rows = (
        orders_query.with_entities(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    type_rows = (
        orders_query.with_entities(Order.order_type, func.count(Order.id))
        .group_by(Order.order_type)
        .all()
    )

    if current_user.role == "manager":
        clients_total = (
            orders_query.with_entities(func.count(func.distinct(Order.client_id)))
            .scalar()
            or 0
        )
        active_managers = 1
    else:
        clients_total = db.query(func.count(Client.id)).scalar() or 0
        active_managers = (
            db.query(func.count(User.id))
            .filter(User.role == "manager", User.is_active.is_(True))
            .scalar()
            or 0
        )

    return {
        "orders_total": orders_query.with_entities(func.count(Order.id)).scalar() or 0,
        "clients_total": clients_total,
        "active_managers": active_managers,
        "total_revenue": Decimal(total_revenue),
        "orders_by_status": {status_name: count for status_name, count in status_rows},
        "orders_by_type": {order_type: count for order_type, count in type_rows},
    }
