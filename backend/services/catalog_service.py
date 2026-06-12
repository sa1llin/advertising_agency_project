from decimal import Decimal

from backend.database import SessionLocal
from backend.models.advertising_space_model import AdvertisingSpace, PricingItem


DEFAULT_SPACES = [
    {
        "title": "Білборд на Центральній площі",
        "space_type": "billboard",
        "location": "Центральна площа, 1",
        "size": "3x6",
        "base_price": Decimal("850.00"),
        "description": "Базова ціна оренди за одну добу.",
    },
    {
        "title": "Білборд на Головній вулиці",
        "space_type": "billboard",
        "location": "Головна вулиця, 24",
        "size": "3x12",
        "base_price": Decimal("1040.00"),
        "description": "Базова ціна оренди за одну добу.",
    },
    {
        "title": "Білборд у житловому районі",
        "space_type": "billboard",
        "location": "Проспект Миру, 80",
        "size": "4x8",
        "base_price": Decimal("610.00"),
        "description": "Базова ціна оренди за одну добу.",
    },
    {
        "title": "LED на Центральній площі",
        "space_type": "led",
        "location": "Центральна площа, 5",
        "size": "6x3",
        "base_price": Decimal("1.20"),
        "description": "Ціна однієї секунди одного показу.",
    },
    {
        "title": "LED біля торгового центру",
        "space_type": "led",
        "location": "ТРЦ, вулиця Соборна, 12",
        "size": "4x2",
        "base_price": Decimal("1.00"),
        "description": "Ціна однієї секунди одного показу.",
    },
]


DEFAULT_PRICES = [
    ("billboard_print", "3x6", "Друк плаката 3x6", "1800.00", "плакат"),
    ("billboard_print", "3x12", "Друк плаката 3x12", "3200.00", "плакат"),
    ("billboard_print", "4x8", "Друк плаката 4x8", "2800.00", "плакат"),
    ("print_product", "business_card", "Візитки", "2.50", "шт"),
    ("print_product", "calendar", "Календарі", "80.00", "шт"),
    ("print_product", "flyer", "Флаєри", "6.00", "шт"),
    ("print_product", "bracelet", "Браслети", "25.00", "шт"),
    ("print_product", "mug", "Чашки", "120.00", "шт"),
    ("print_product", "other", "Інша продукція", "1.00", "шт"),
    ("print_material", "coated_paper", "Крейдований папір", "0.50", "шт"),
    ("print_material", "cardboard", "Картон", "1.50", "шт"),
    ("print_material", "vinyl", "Вініл", "3.00", "шт"),
    ("print_material", "silicone", "Силікон", "10.00", "шт"),
    ("print_material", "ceramic", "Кераміка", "30.00", "шт"),
    ("print_material", "other", "Інший матеріал", "0.00", "шт"),
    ("print_size", "small", "Малий", "0.00", "шт"),
    ("print_size", "medium", "Середній", "2.00", "шт"),
    ("print_size", "large", "Великий", "5.00", "шт"),
    ("print_size", "custom", "Індивідуальний", "0.00", "шт"),
    ("print_color", "black_white", "Чорно-біла", "0.00", "шт"),
    ("print_color", "one_side_color", "Одностороння кольорова", "0.75", "шт"),
    ("print_color", "full_color", "Повноколірна", "1.50", "шт"),
]


def seed_order_catalog(db=None) -> None:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        if session.query(AdvertisingSpace.id).first() is None:
            session.add_all(AdvertisingSpace(**item) for item in DEFAULT_SPACES)

        existing = {
            (category, code)
            for category, code in session.query(
                PricingItem.category,
                PricingItem.code,
            ).all()
        }
        for category, code, label, amount, unit_name in DEFAULT_PRICES:
            if (category, code) not in existing:
                session.add(
                    PricingItem(
                        category=category,
                        code=code,
                        label=label,
                        amount=Decimal(amount),
                        unit_name=unit_name,
                    )
                )
        session.commit()
    finally:
        if owns_session:
            session.close()
