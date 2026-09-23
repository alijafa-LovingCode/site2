from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models import ActivityLog, User


def log_activity(
    db: Session,
    user: Optional[User],
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    entry = ActivityLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
