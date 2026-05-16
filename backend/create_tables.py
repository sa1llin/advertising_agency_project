from backend.database import Base, engine
from backend import models  # noqa: F401


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Таблиці створено успішно.")
