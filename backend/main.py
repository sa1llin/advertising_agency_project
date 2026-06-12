from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import check_database_connection, get_db
from backend.routers.clients_router import router as clients_router
from backend.routers.orders_router import router as orders_router
from backend.routers.calculator_router import router as calculator_router
from backend.routers.analytics_router import router as analytics_router
from backend.routers.auth_router import router as auth_router
from backend.routers.logs_router import router as logs_router
from backend.routers.users_router import router as users_router
from backend.routers.catalog_router import router as catalog_router
from backend.routers.applications_router import router as applications_router


app = FastAPI(
    title="Advertising Agency API",
    description="Backend API для дипломного проєкта рекламного агентства",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients_router)
app.include_router(orders_router)
app.include_router(calculator_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(logs_router)
app.include_router(analytics_router)
app.include_router(catalog_router)
app.include_router(applications_router)



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
