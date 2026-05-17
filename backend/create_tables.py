from backend.database import Base, engine

from backend.models.client_model import Client
from backend.models.user_model import User
from backend.models.service_model import Service
from backend.models.order_model import Order
from backend.models.payment_model import Payment


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы")


if __name__ == "__main__":
    create_tables()