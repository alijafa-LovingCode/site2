from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models import Exam, StudyTask, User
from app.services.jalali import gregorian_to_jalali_long, today_local
from app.services.messages_seed import get_message_for_date
from app.services.planner_engine import to_days_label

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/dashboard")
def student_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = today_local()

    today_tasks = db.execute(
        select(StudyTask).where(StudyTask.date == today).order_by(StudyTask.priority)
    ).scalars().all()

    next_exam = db.execute(
        select(Exam).where(Exam.exam_date >= today).order_by(Exam.exam_date).limit(1)
    ).scalar_one_or_none()

    msg = get_message_for_date(db, today)

    return {
        "greeting": "سلام مهرسا 👋",
        "today_date_fa": gregorian_to_jalali_long(today),
        "today_tasks": [
            {
                "id": t.id,
                "subject_name": t.subject.name if t.subject else "",
                "subject_color": t.subject.color if t.subject else "#999999",
                "duration_minutes": t.duration_minutes,
                "is_completed": t.is_completed,
                "task": t.task,
            }
            for t in today_tasks
        ],
        "today_completed": sum(1 for t in today_tasks if t.is_completed),
        "today_total": len(today_tasks),
        "next_exam": (
            {
                "name": next_exam.name,
                "subject_name": next_exam.subject.name if next_exam.subject else None,
                "exam_date": next_exam.exam_date.isoformat(),
                "exam_date_fa": gregorian_to_jalali_long(next_exam.exam_date),
                "days_remaining": (next_exam.exam_date - today).days,
                "days_label": to_days_label((next_exam.exam_date - today).days),
            }
            if next_exam
            else None
        ),
        "daily_message": msg.text if msg else None,
    }
