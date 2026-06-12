from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.advertising_space_model import AdvertisingSpace, PricingItem
from backend.models.user_model import User
from backend.schemas.catalog_schema import OrderCatalogResponse

router = APIRouter(prefix="/catalog", tags=["Catalog"])


def build_order_catalog(
    db: Session,
    *,
    include_inactive: bool = False,
) -> OrderCatalogResponse:
    spaces_query = db.query(AdvertisingSpace)
    if not include_inactive:
        spaces_query = spaces_query.filter(AdvertisingSpace.is_active.is_(True))
    spaces = spaces_query.order_by(
        AdvertisingSpace.space_type,
        AdvertisingSpace.location,
    ).all()
    prices = (
        db.query(PricingItem)
        .filter(PricingItem.is_active.is_(True))
        .order_by(PricingItem.category, PricingItem.label)
        .all()
    )
    return OrderCatalogResponse(
        advertising_spaces=spaces,
        pricing_items=prices,
        loaded_at=datetime.now(),
    )


@router.get("/public-order-options", response_model=OrderCatalogResponse)
def get_public_order_options(db: Session = Depends(get_db)):
    return build_order_catalog(db)


@router.get("/order-options", response_model=OrderCatalogResponse)
def get_order_options(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return build_order_catalog(db, include_inactive=include_inactive)
