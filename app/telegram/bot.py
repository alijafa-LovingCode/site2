"""
Telegram bot logic: Persian-only.

Two responsibilities:
  1. `send_telegram_message()` -- used by the scheduler and admin routes to
     push proactive messages (daily plan, exam reminders, motivational
     messages) using plain HTTP calls to the Telegram Bot API.
  2. `build_application()` -- a python-telegram-bot Application used by the
     worker process to answer commands and free-text questions from Ali/
     Mehrsa (polling mode, so it keeps working even when nobody has the
     website open).

All responses are generated from real database data -- nothing here is
hard-coded schedule content.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import session_scope
from app.models import Exam, StudyTask, TelegramSettings
from app.services.jalali import gregorian_to_jalali_long, today_local, to_fa_digits
from app.services.messages_seed import get_message_for_date
from app.services.planner_engine import to_days_label

logger = logging.getLogger("telegram_bot")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


def get_telegram_settings(db: Session) -> Optional[TelegramSettings]:
    return db.execute(select(TelegramSettings)).scalars().first()


async def send_telegram_message(text: str, db: Optional[Session] = None) -> bool:
    """Send a Persian message to the configured chat. Returns True on success."""
    owns_session = db is None
    if owns_session:
        from app.database import SessionLocal

        db = SessionLocal()
    try:
        cfg = get_telegram_settings(db)
        if not cfg or not cfg.is_enabled or not cfg.bot_token or not cfg.chat_id:
            return False
        url = TELEGRAM_API_BASE.format(token=cfg.bot_token) + "/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={"chat_id": cfg.chat_id, "text": text})
            if resp.status_code != 200:
                logger.warning("Telegram send failed with status %s", resp.status_code)
                return False
            return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram send error: %s", type(exc).__name__)
        return False
    finally:
        if owns_session:
            db.close()


# ------------------------------------------------------------- Builders ---
def build_today_plan_text(db: Session, target_date: Optional[date] = None) -> str:
    tz = settings.telegram_timezone
    target_date = target_date or today_local(tz)
    tasks = db.execute(
        select(StudyTask).where(StudyTask.date == target_date).order_by(StudyTask.priority)
    ).scalars().all()

    if not tasks:
        return f"برای {gregorian_to_jalali_long(target_date)} هنوز برنامه‌ای ثبت نشده مهرسا جان 🌱"

    lines = [f"برنامه {gregorian_to_jalali_long(target_date)}:", ""]
    for t in tasks:
        subject_name = t.subject.name if t.subject else "نامشخص"
        status = "✅" if t.is_completed else "📚"
        lines.append(f"{status} {subject_name} — {to_fa_digits(t.duration_minutes)} دقیقه")
    lines.append("")
    lines.append("موفق باشی مهرسا 🌱")
    return "\n".join(lines)


def build_next_exam_text(db: Session) -> str:
    tz = settings.telegram_timezone
    today = today_local(tz)
    exam = db.execute(
        select(Exam).where(Exam.exam_date >= today).order_by(Exam.exam_date).limit(1)
    ).scalar_one_or_none()
    if not exam:
        return "فعلاً آزمونی در برنامه ثبت نشده 🌸"
    days_remaining = (exam.exam_date - today).days
    subject_name = exam.subject.name if exam.subject else ""
    prefix = f"{subject_name} — " if subject_name else ""
    return f"آزمون بعدی: {prefix}{exam.name}\n{to_days_label(days_remaining)} ({to_fa_digits(days_remaining)} روز)"


def build_days_until_subject_exam(db: Session, subject_name: str) -> str:
    tz = settings.telegram_timezone
    today = today_local(tz)
    exam = db.execute(
        select(Exam)
        .join(Exam.subject)
        .where(Exam.exam_date >= today)
        .order_by(Exam.exam_date)
    ).scalars().all()
    for e in exam:
        if e.subject and subject_name in e.subject.name:
            days_remaining = (e.exam_date - today).days
            return f"تا آزمون {e.subject.name} {to_fa_digits(days_remaining)} روز مونده."
    return f"آزمونی برای {subject_name} در برنامه پیدا نکردم."


def build_resources_text(db: Session, limit: int = 8) -> str:
    from app.models import Resource

    resources = db.execute(select(Resource).order_by(Resource.id.desc()).limit(limit)).scalars().all()
    if not resources:
        return "هنوز منبعی ثبت نشده."
    lines = ["📖 آخرین منابع:", ""]
    for r in resources:
        lines.append(f"• {r.title}")
    return "\n".join(lines)


def build_status_text(db: Session) -> str:
    tz = settings.telegram_timezone
    today = today_local(tz)
    tasks = db.execute(select(StudyTask).where(StudyTask.date == today)).scalars().all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.is_completed)
    if total == 0:
        return "برای امروز برنامه‌ای ثبت نشده."
    return f"وضعیت امروز: {to_fa_digits(done)} از {to_fa_digits(total)} کار انجام شده ✅"


def build_today_weekday_text() -> str:
    tz = settings.telegram_timezone
    today = today_local(tz)
    return f"امروز {gregorian_to_jalali_long(today)} است."


def build_reminder_text(db: Session) -> str:
    today = today_local(settings.telegram_timezone)
    msg = get_message_for_date(db, today)
    plan_text = build_today_plan_text(db, today)
    parts = ["مهرسا جان، برنامه امروزت رو انجام دادی؟ 📚", "", plan_text]
    if msg:
        parts.extend(["", msg.text])
    return "\n".join(parts)


def build_exam_countdown_reminder(db: Session) -> Optional[str]:
    tz = settings.telegram_timezone
    today = today_local(tz)
    exam = db.execute(
        select(Exam).where(Exam.exam_date >= today).order_by(Exam.exam_date).limit(1)
    ).scalar_one_or_none()
    if not exam:
        return None
    days_remaining = (exam.exam_date - today).days
    if days_remaining not in (0, 1, 3, 7):
        return None
    subject_name = exam.subject.name if exam.subject else ""
    prefix = f"{subject_name} — " if subject_name else ""
    return f"⏰ یادآوری آزمون: {prefix}{exam.name}\n{to_days_label(days_remaining)}. آماده‌ای مهرسا؟ 💪"


# ---------------------------------------------------------- Free-text QA ---
def answer_free_text_question(db: Session, text: str) -> Optional[str]:
    """Very small Persian keyword matcher for common date/plan questions.
    Always queries the database -- never hard-coded answers."""
    t = text.strip()

    if "امتحان بعدی" in t or "آزمون بعدی" in t:
        return build_next_exam_text(db)

    if "چند روز" in t and ("امتحان" in t or "آزمون" in t):
        for subject_name in ["ریاضی", "فیزیک", "شیمی", "زیست", "ادبیات", "عربی", "دینی", "زبان"]:
            if subject_name in t:
                return build_days_until_subject_exam(db, subject_name)
        return build_next_exam_text(db)

    if "امروز چه روزی" in t or "امروز چندشنبه" in t or "چه روزیه" in t:
        return build_today_weekday_text()

    if "برنامه امروز" in t:
        return build_today_plan_text(db)

    if "وضعیت" in t:
        return build_status_text(db)

    return None
