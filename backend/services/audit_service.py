import json
from typing import Any

from sqlalchemy.orm import Session

from backend.models.log_model import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    *,
    entity_name: str | None = None,
    entity_id: int | None = None,
    details: dict[str, Any] | str | None = None,
) -> AuditLog:
    serialized_details = (
        json.dumps(details, ensure_ascii=False, default=str)
        if isinstance(details, dict)
        else details
    )
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        details=serialized_details,
    )
    db.add(entry)
    return entry
