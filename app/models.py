"""
SQLAlchemy ORM models.

Tables:
  users, subjects, study_tasks, weekly_plans, exams, resources,
  daily_messages, message_deliveries, chat_messages, telegram_settings,
  notification_settings, cycle_entries, system_settings, activity_logs
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"


class ResourceTypeEnum(str, enum.Enum):
    PDF = "PDF"
    BOOK = "کتاب"
    NOTE = "جزوه"
    LINK = "لینک خارجی"
    VIDEO = "ویدئو"


class MessageCategoryEnum(str, enum.Enum):
    MOTIVATIONAL = "انگیزشی"
    STUDY = "مطالعه"
    EXAM = "آزمون"
    CALM = "آرامش"
    REST = "استراحت"
    DAILY_POSITIVE = "مثبت روزانه"


class SenderEnum(str, enum.Enum):
    ALI = "ALI"
    MEHRSA = "MEHRSA"


# ---------------------------------------------------------------- Users ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ------------------------------------------------------------- Subjects ---
class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1 (highest) - 5 (lowest)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    color: Mapped[str] = mapped_column(String(20), default="#6C63FF")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list["StudyTask"]] = relationship(back_populates="subject")
    exams: Mapped[list["Exam"]] = relationship(back_populates="subject")
    resources: Mapped[list["Resource"]] = relationship(back_populates="subject")


# ---------------------------------------------------------- Study Tasks ---
class StudyTask(Base):
    """A single study task, belonging to a specific calendar date.
    Used both for the "daily plan" and as the building block of the
    weekly planner (a week is simply 7 consecutive dates)."""

    __tablename__ = "study_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    chapter: Mapped[str | None] = mapped_column(String(200), nullable=True)
    task: Mapped[str | None] = mapped_column(String(300), nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "HH:MM"
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    break_minutes: Mapped[int] = mapped_column(Integer, default=10)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    exam_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subject: Mapped["Subject"] = relationship(back_populates="tasks")


# --------------------------------------------------- Next-day subject asks
class NextDaySelection(Base):
    """Stores Mehrsa's answer to 'what subjects do you have tomorrow?'"""

    __tablename__ = "next_day_selections"
    __table_args__ = (UniqueConstraint("date", "subject_id", name="uq_nextday_date_subject"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)  # the target (tomorrow's) date
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------- Weekly plans
class WeeklyPlan(Base):
    """A named container for a week (e.g. week starting Saturday X)."""

    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start_date: Mapped[Date] = mapped_column(Date, nullable=False, unique=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------------ Exams
class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    exam_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    exam_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=3)  # 1 highest - 5 lowest
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subject: Mapped["Subject"] = relationship(back_populates="exams")


# --------------------------------------------------------------- Resources
class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)  # پایه
    chapter: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[ResourceTypeEnum] = mapped_column(
        Enum(ResourceTypeEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=ResourceTypeEnum.LINK,
    )
    is_downloadable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subject: Mapped["Subject"] = relationship(back_populates="resources")


# --------------------------------------------------------- Daily messages
class DailyMessage(Base):
    """Pool of ~30 motivational/reminder messages used in the 29/30 day
    non-repeating cycle."""

    __tablename__ = "daily_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[MessageCategoryEnum] = mapped_column(
        Enum(MessageCategoryEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=MessageCategoryEnum.MOTIVATIONAL,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MessageDelivery(Base):
    """Tracks which message was sent on which date, so the cycle does not
    repeat until the pool is exhausted."""

    __tablename__ = "message_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("daily_messages.id", ondelete="CASCADE"))
    delivered_date: Mapped[Date] = mapped_column(Date, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ----------------------------------------------------------- Chat messages
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[SenderEnum] = mapped_column(Enum(SenderEnum), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


# -------------------------------------------------------- Telegram settings
class TelegramSettings(Base):
    """Single-row table holding the current Telegram configuration."""

    __tablename__ = "telegram_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_time: Mapped[str] = mapped_column(String(5), default="08:00")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tehran")
    daily_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    exam_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    motivational_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cycle_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------- Notification settings
class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ask_next_day_subjects_time: Mapped[str] = mapped_column(String(5), default="20:00")
    daily_completion_check_time: Mapped[str] = mapped_column(String(5), default="21:30")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ------------------------------------------------------------- Cycle entries
class CycleEntry(Base):
    """Private personal cycle-tracking data for Mehrsa.
    Estimates only -- not a medical tool."""

    __tablename__ = "cycle_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    cycle_length_days: Mapped[int] = mapped_column(Integer, default=28)
    period_length_days: Mapped[int] = mapped_column(Integer, default=6)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------- System settings
class SystemSetting(Base):
    """Generic key/value store for small configuration values that Ali can
    change from the admin panel (e.g. study hours per day, message cycle
    length, current index in the message cycle)."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --------------------------------------------------------------- Activity logs
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
