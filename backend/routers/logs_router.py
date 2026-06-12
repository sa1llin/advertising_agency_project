from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import require_admin
from backend.models.log_model import AuditLog
from backend.models.user_model import User


router = APIRouter(prefix="/logs", tags=["Audit logs"])


@router.get("/")
def get_logs(
    user_id: int | None = Query(default=None, gt=0),
    action: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog, User.username).outerjoin(
        User,
        AuditLog.user_id == User.id,
    )
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)

    rows = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": entry.id,
            "user_id": entry.user_id,
            "username": username,
            "action": entry.action,
            "entity_name": entry.entity_name,
            "entity_id": entry.entity_id,
            "details": entry.details,
            "created_at": entry.created_at,
        }
        for entry, username in rows
    ]
