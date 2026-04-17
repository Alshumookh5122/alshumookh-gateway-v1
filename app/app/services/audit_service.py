from sqlalchemy.orm import Session

from app.models import AuditLog
from app.utils import safe_json_dumps, utc_now


def add_audit(
    db: Session,
    event_type: str,
    reference_id: str | None = None,
    details: dict | None = None,
) -> None:
    row = AuditLog(
        event_type=event_type,
        reference_id=reference_id,
        details_json=safe_json_dumps(details or {}),
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
