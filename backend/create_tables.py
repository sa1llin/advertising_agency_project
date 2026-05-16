from backend.database import Base, engine
from backend.models.client_model import Client


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Таблиці створено успішно!")