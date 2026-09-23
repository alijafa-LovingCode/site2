from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import CycleEntry, RoleEnum, User
from app.schemas import CycleEntryCreate, CycleEntryOut, CyclePredictionOut
from app.services.activity_log import log_activity

router = APIRouter(prefix="/api/cycle", tags=["cycle"])


def _ensure_access(user: User) -> None:
    """Only Mehrsa (STUDENT) may access her own cycle data. Ali (ADMIN) may
    only access it if explicitly enabled via CYCLE_ADMIN_ACCESS."""
    if user.role == RoleEnum.STUDENT:
        return
    if user.role == RoleEnum.ADMIN and settings.cycle_admin_access:
        return
    raise HTTPException(status_code=403, detail="دسترسی به این بخش محدود است.")


@router.get("/entries", response_model=List[CycleEntryOut])
def list_entries(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_access(user)
    entries = db.execute(select(CycleEntry).order_by(CycleEntry.start_date.desc())).scalars().all()
    return entries


@router.post("/entries", response_model=CycleEntryOut)
def create_entry(payload: CycleEntryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_access(user)
    entry = CycleEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    log_activity(db, user, "cycle_entry_added")
    return entry


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_access(user)
    entry = db.get(CycleEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="یافت نشد.")
    db.delete(entry)
    db.commit()
    log_activity(db, user, "cycle_entry_deleted")
    return {"message": "حذف شد."}


@router.get("/prediction", response_model=CyclePredictionOut)
def get_prediction(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_access(user)
    entries = db.execute(select(CycleEntry).order_by(CycleEntry.start_date.desc())).scalars().all()
    if not entries:
        return CyclePredictionOut(
            last_start_date=None,
            estimated_next_start=None,
            estimated_fertile_window_start=None,
            estimated_fertile_window_end=None,
            average_cycle_length=None,
        )

    latest = entries[0]
    lengths = [e.cycle_length_days for e in entries if e.cycle_length_days]
    avg_length = sum(lengths) / len(lengths) if lengths else latest.cycle_length_days

    next_start = latest.start_date + timedelta(days=round(avg_length))
    fertile_start = next_start - timedelta(days=16)
    fertile_end = next_start - timedelta(days=12)

    return CyclePredictionOut(
        last_start_date=latest.start_date,
        estimated_next_start=next_start,
        estimated_fertile_window_start=fertile_start,
        estimated_fertile_window_end=fertile_end,
        average_cycle_length=round(avg_length, 1),
    )
