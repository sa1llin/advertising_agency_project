from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db, check_database_connection

app = FastAPI(
    title="Advertising Agency API",
    description="Backend API для дипломного проєкта рекламного агентства",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "message": "Backend рекламного агентства запущен"
    }

@app.get("/health")
def health_check():
    is_connected = check_database_connection()
    return {
        "backend": "ok",
        "database": "connected" if is_connected else "error"
    }


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    
    result = db.execute(text("select database()"))
    database_name = result.scalar()
    return {
        "current_database": database_name
    }
