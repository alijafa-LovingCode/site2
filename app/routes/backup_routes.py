from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.database import get_db
from app.models import User
from app.services.activity_log import log_activity
from app.services.backup_service import create_backup

router = APIRouter(prefix="/api/admin/backup", tags=["backup"])


@router.get("/export")
def export_backup(
    include_cycle_data: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Returns a downloadable JSON snapshot of the site's data (subjects,
    tasks, exams, resources, messages, chat, settings). Password hashes
    and the Telegram bot token are never included."""
    payload = create_backup(db, include_cycle_data=include_cycle_data)
    log_activity(db, admin, "backup_exported", details=f"include_cycle_data={include_cycle_data}")

    filename = f"mehrsa-planner-backup-{payload['generated_at'][:10]}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
