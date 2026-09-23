from datetime import date, timedelta

from app.database import SessionLocal
from app.models import Exam, StudyTask, Subject
from app.telegram.bot import (
    answer_free_text_question,
    build_next_exam_text,
    build_today_plan_text,
)


def test_build_today_plan_text_empty():
    with SessionLocal() as db:
        far_future = date(2099, 1, 1)
        text = build_today_plan_text(db, far_future)
        assert "هنوز برنامه‌ای ثبت نشده" in text


def test_build_today_plan_text_with_tasks():
    with SessionLocal() as db:
        subject = db.query(Subject).first()
        target = date(2030, 5, 10)
        task = StudyTask(subject_id=subject.id, date=target, duration_minutes=90)
        db.add(task)
        db.commit()

        text = build_today_plan_text(db, target)
        assert subject.name in text
        assert "۹۰" in text or "90" in text
        assert "مهرسا" in text

        db.delete(task)
        db.commit()


def test_build_next_exam_text_uses_database():
    with SessionLocal() as db:
        subject = db.query(Subject).first()
        exam_date = date.today() + timedelta(days=3)
        exam = Exam(name="آزمون تست تلگرام", subject_id=subject.id, exam_date=exam_date, importance=1)
        db.add(exam)
        db.commit()

        text = build_next_exam_text(db)
        assert "آزمون تست تلگرام" in text

        db.delete(exam)
        db.commit()


def test_free_text_question_next_exam():
    with SessionLocal() as db:
        answer = answer_free_text_question(db, "امتحان بعدی من کیه؟")
        assert answer is not None


def test_free_text_question_unrelated_returns_none():
    with SessionLocal() as db:
        answer = answer_free_text_question(db, "سلام حالت چطوره؟")
        assert answer is None
