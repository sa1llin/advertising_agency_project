from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import check_database_connection, get_db
from backend.routers.clients_router import router as clients_router


app = FastAPI(
    title="Advertising Agency API",
    description="Backend API для дипломного проєкта рекламного агентства",
    version="1.0.0",
)

app.include_router(clients_router)


@app.get("/")
def root():
    return {
        "message": "Backend рекламного агентства запущено успішно!"
    }


@app.get("/health")
def health_check():
    is_connected = check_database_connection()

    return {
        "backend": "ok",
        "database": "connected" if is_connected else "error",
    }


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    result = db.execute(text("select database()"))
    database_name = result.scalar()

    return {
        "current_database": database_name
    }