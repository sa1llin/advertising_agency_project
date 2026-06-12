from sqlalchemy import inspect, text

from backend.database import Base, engine

from backend.models.client_model import Client
from backend.models.user_model import User
from backend.models.service_model import Service
from backend.models.order_model import Order
from backend.models.payment_model import Payment
from backend.models.log_model import AuditLog
from backend.models.expense_model import Expense
from backend.models.advertising_space_model import AdvertisingSpace, PricingItem
from backend.models.order_segment_model import OrderSegment
from backend.models.application_model import WebsiteApplication
from backend.services.catalog_service import seed_order_catalog


def create_tables():
    Base.metadata.create_all(bind=engine)
    ensure_application_columns()
    seed_order_catalog()
    print("Таблицы успешно созданы")


def ensure_application_columns() -> None:
    inspector = inspect(engine)
    if "website_applications" not in inspector.get_table_names():
        return

    column_names = {
        column["name"]
        for column in inspector.get_columns("website_applications")
    }
    statements: list[str] = []
    if "source" not in column_names:
        statements.append(
            "ALTER TABLE website_applications "
            "ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'contact'"
        )
    if "calculation_data" not in column_names:
        column_type = "JSON" if engine.dialect.name == "mysql" else "TEXT"
        statements.append(
            "ALTER TABLE website_applications "
            f"ADD COLUMN calculation_data {column_type} NULL"
        )

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))


if __name__ == "__main__":
    create_tables()
