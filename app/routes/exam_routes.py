from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.database import get_db
from app.models import Exam, User
from app.schemas import ExamCreate, ExamOut, ExamUpdate
from app.services.activity_log import log_activity
from app.services.jalali import today_local

router = APIRouter(prefix="/api/exams", tags=["exams"])


def _exam_to_out(e: Exam, today: date) -> ExamOut:
    return ExamOut(
        id=e.id,
        name=e.name,
        subject_id=e.subject_id,
        subject_name=e.subject.name if e.subject else None,
        exam_date=e.exam_date,
        exam_time=e.exam_time,
        description=e.description,
        importance=e.importance,
        days_remaining=(e.exam_date - today).days,
    )


@router.get("", response_model=List[ExamOut])
def list_exams(upcoming_only: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = today_local()
    query = select(Exam).order_by(Exam.exam_date)
    if upcoming_only:
        query = query.where(Exam.exam_date >= today)
    exams = db.execute(query).scalars().all()
    return [_exam_to_out(e, today) for e in exams]


@router.get("/next", response_model=ExamOut)
def next_exam(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = today_local()
    exam = db.execute(select(Exam).where(Exam.exam_date >= today).order_by(Exam.exam_date).limit(1)).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="آزمونی ثبت نشده است.")
    return _exam_to_out(exam, today)


@router.post("", response_model=ExamOut)
def create_exam(payload: ExamCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    exam = Exam(**payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    log_activity(db, admin, "exam_created", details=exam.name)
    return _exam_to_out(exam, today_local())


@router.put("/{exam_id}", response_model=ExamOut)
def update_exam(exam_id: int, payload: ExamUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="آزمون پیدا نشد.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    log_activity(db, admin, "exam_updated", details=exam.name)
    return _exam_to_out(exam, today_local())


@router.delete("/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="آزمون پیدا نشد.")
    db.delete(exam)
    db.commit()
    log_activity(db, admin, "exam_deleted", details=exam.name)
    return {"message": "آزمون حذف شد."}
