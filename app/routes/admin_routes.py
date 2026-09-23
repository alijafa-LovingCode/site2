from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.database import get_db
from app.models import ActivityLog, Exam, Resource, StudyTask, Subject, SystemSetting, TelegramSettings, User
from app.schemas import ActivityLogOut, AdminDashboardOut
from app.services.activity_log import log_activity
from app.services.jalali import today_local

router = APIRouter(prefix="/api/admin", tags=["admin"])

DEFAULT_SYSTEM_SETTINGS = {
    "daily_budget_minutes": "240",
    "message_cycle_length": "30",
}


@router.get("/dashboard", response_model=AdminDashboardOut)
def dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    today = today_local()

    today_tasks = db.execute(select(StudyTask).where(StudyTask.date == today)).scalars().all()
    upcoming_exams_count = db.execute(
        select(func.count()).select_from(Exam).where(Exam.exam_date >= today)
    ).scalar_one()
    telegram_cfg = db.execute(select(TelegramSettings)).scalars().first()
    resources_count = db.execute(select(func.count()).select_from(Resource)).scalar_one()
    active_subjects = db.execute(
        select(func.count()).select_from(Subject).where(Subject.is_active.is_(True))
    ).scalar_one()

    recent_logs = db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(10)
    ).scalars().all()

    return AdminDashboardOut(
        today_tasks_total=len(today_tasks),
        today_tasks_completed=sum(1 for t in today_tasks if t.is_completed),
        upcoming_exams=upcoming_exams_count,
        telegram_enabled=bool(telegram_cfg and telegram_cfg.is_enabled),
        resources_count=resources_count,
        active_subjects=active_subjects,
        recent_activity=[
            {
                "action": log.action,
                "username": log.username,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent_logs
        ],
    )


@router.get("/logs", response_model=List[ActivityLogOut])
def get_logs(limit: int = 100, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    logs = db.execute(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)).scalars().all()
    return logs


@router.get("/settings")
def get_system_settings(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.execute(select(SystemSetting)).scalars().all()
    values = {r.key: r.value for r in rows}
    for key, default in DEFAULT_SYSTEM_SETTINGS.items():
        values.setdefault(key, default)
    return values


@router.put("/settings")
def update_system_settings(payload: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    for key, value in payload.items():
        row = db.get(SystemSetting, key)
        if row:
            row.value = str(value)
        else:
            db.add(SystemSetting(key=key, value=str(value)))
    db.commit()
    log_activity(db, admin, "system_settings_updated", details=str(payload))
    return {"message": "تنظیمات ذخیره شد."}


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.execute(select(User)).scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "role": u.role.value,
            "is_active": u.is_active,
        }
        for u in users
    ]
