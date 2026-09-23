from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ai_client import explain_plan
from app.auth.deps import get_current_user, require_admin
from app.database import get_db
from app.models import NextDaySelection, RoleEnum, StudyTask, Subject, User
from app.schemas import (
    NextDaySelectionRequest,
    StudyTaskCreate,
    StudyTaskOut,
    StudyTaskUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
)
from app.services.activity_log import log_activity
from app.services.jalali import gregorian_to_jalali_long, persian_weekday_name, today_local
from app.services.planner_engine import generate_daily_plan, persist_plan

router = APIRouter(tags=["planner"])


# --------------------------------------------------------------- Subjects
@router.get("/api/subjects", response_model=List[SubjectOut])
def list_subjects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subjects = db.execute(select(Subject).order_by(Subject.priority, Subject.name)).scalars().all()
    return subjects


@router.post("/api/subjects", response_model=SubjectOut)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.execute(select(Subject).where(Subject.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="این درس قبلاً ثبت شده است.")
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    log_activity(db, admin, "subject_created", details=subject.name)
    return subject


@router.put("/api/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    log_activity(db, admin, "subject_updated", details=subject.name)
    return subject


@router.delete("/api/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد.")
    db.delete(subject)
    db.commit()
    log_activity(db, admin, "subject_deleted", details=subject.name)
    return {"message": "درس حذف شد."}


# ----------------------------------------------------------------- Tasks
def _task_to_out(t: StudyTask) -> StudyTaskOut:
    return StudyTaskOut(
        id=t.id,
        subject_id=t.subject_id,
        subject_name=t.subject.name if t.subject else "",
        subject_color=t.subject.color if t.subject else "#999999",
        date=t.date,
        chapter=t.chapter,
        task=t.task,
        start_time=t.start_time,
        duration_minutes=t.duration_minutes,
        break_minutes=t.break_minutes,
        priority=t.priority,
        exam_relevant=t.exam_relevant,
        is_completed=t.is_completed,
        is_ai_generated=t.is_ai_generated,
        notes=t.notes,
    )


@router.get("/api/tasks", response_model=List[StudyTaskOut])
def list_tasks(
    start_date: date,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    end_date = end_date or start_date
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="بازه تاریخ نامعتبر است.")
    tasks = db.execute(
        select(StudyTask).where(StudyTask.date >= start_date, StudyTask.date <= end_date).order_by(StudyTask.date, StudyTask.priority)
    ).scalars().all()
    return [_task_to_out(t) for t in tasks]


@router.get("/api/tasks/today", response_model=List[StudyTaskOut])
def today_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = today_local()
    tasks = db.execute(select(StudyTask).where(StudyTask.date == today).order_by(StudyTask.priority)).scalars().all()
    return [_task_to_out(t) for t in tasks]


@router.get("/api/tasks/week")
def week_tasks(week_start: date, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Returns 7 days of tasks starting at `week_start`, grouped by Persian weekday."""
    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        tasks = db.execute(select(StudyTask).where(StudyTask.date == d).order_by(StudyTask.priority)).scalars().all()
        days.append(
            {
                "date": d.isoformat(),
                "weekday_fa": persian_weekday_name(d),
                "date_fa": gregorian_to_jalali_long(d),
                "tasks": [_task_to_out(t).model_dump(mode="json") for t in tasks],
            }
        )
    return {"week_start": week_start.isoformat(), "days": days}


@router.post("/api/tasks", response_model=StudyTaskOut)
def create_task(payload: StudyTaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subject = db.get(Subject, payload.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد.")
    task = StudyTask(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    log_activity(db, user, "task_created", details=f"{subject.name} - {payload.date}")
    return _task_to_out(task)


@router.put("/api/tasks/{task_id}", response_model=StudyTaskOut)
def update_task(task_id: int, payload: StudyTaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(StudyTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="کار پیدا نشد.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    action = "task_completed" if payload.is_completed else "task_updated"
    log_activity(db, user, action, details=str(task_id))
    return _task_to_out(task)


@router.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(StudyTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="کار پیدا نشد.")
    db.delete(task)
    db.commit()
    log_activity(db, user, "task_deleted", details=str(task_id))
    return {"message": "حذف شد."}


# --------------------------------------------------------- Next-day flow
@router.get("/api/next-day-selection")
def get_next_day_selection(target_date: date, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(NextDaySelection).where(NextDaySelection.date == target_date)).scalars().all()
    return {"date": target_date.isoformat(), "subject_ids": [r.subject_id for r in rows]}


@router.post("/api/next-day-selection")
def set_next_day_selection(payload: NextDaySelectionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(
        NextDaySelection.__table__.delete().where(NextDaySelection.date == payload.date)
    )
    for subject_id in payload.subject_ids:
        subject = db.get(Subject, subject_id)
        if subject:
            db.add(NextDaySelection(date=payload.date, subject_id=subject_id))
    db.commit()
    log_activity(db, user, "next_day_selection_set", details=f"{payload.date}: {payload.subject_ids}")
    return {"message": "درس‌های فردا ثبت شد."}


# ------------------------------------------------------- Plan generation
@router.post("/api/planner/generate")
async def generate_plan(
    target_date: date,
    daily_budget_minutes: int = 240,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    selection = db.execute(select(NextDaySelection).where(NextDaySelection.date == target_date)).scalars().all()
    subject_ids = [s.subject_id for s in selection]
    if not subject_ids:
        raise HTTPException(status_code=400, detail="ابتدا درس‌های آن روز را انتخاب کنید.")

    items = generate_daily_plan(db, target_date, subject_ids, daily_budget_minutes)
    if not items:
        raise HTTPException(status_code=400, detail="امکان تولید برنامه وجود نداشت.")

    created = persist_plan(db, target_date, items)
    log_activity(db, user, "plan_generated", details=f"{target_date}: {len(created)} tasks")

    subject_lines = [f"{i.subject_name} — {i.duration_minutes} دقیقه" for i in items]
    explanation = await explain_plan(subject_lines, gregorian_to_jalali_long(target_date))

    return {
        "date": target_date.isoformat(),
        "date_fa": gregorian_to_jalali_long(target_date),
        "tasks": [_task_to_out(t).model_dump(mode="json") for t in created],
        "explanation": explanation,
    }
