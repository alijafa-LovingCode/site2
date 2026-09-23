from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- Auth ---
class LoginRequest(BaseModel):
    username: str  # "ali" | "mehrsa"
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    display_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# ------------------------------------------------------------- Subjects ---
class SubjectCreate(BaseModel):
    name: str
    priority: int = 3
    difficulty: int = 3
    color: str = "#6C63FF"


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    difficulty: Optional[int] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectOut(BaseModel):
    id: int
    name: str
    priority: int
    difficulty: int
    color: str
    is_active: bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------- Tasks ---
class StudyTaskCreate(BaseModel):
    subject_id: int
    date: date
    chapter: Optional[str] = None
    task: Optional[str] = None
    start_time: Optional[str] = None
    duration_minutes: int = 60
    break_minutes: int = 10
    priority: int = 3
    exam_relevant: bool = False
    notes: Optional[str] = None


class StudyTaskUpdate(BaseModel):
    chapter: Optional[str] = None
    task: Optional[str] = None
    start_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    break_minutes: Optional[int] = None
    priority: Optional[int] = None
    exam_relevant: Optional[bool] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None


class StudyTaskOut(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    subject_color: str
    date: date
    chapter: Optional[str]
    task: Optional[str]
    start_time: Optional[str]
    duration_minutes: int
    break_minutes: int
    priority: int
    exam_relevant: bool
    is_completed: bool
    is_ai_generated: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class NextDaySelectionRequest(BaseModel):
    date: date
    subject_ids: List[int]


# ----------------------------------------------------------------- Exams ---
class ExamCreate(BaseModel):
    name: str
    subject_id: Optional[int] = None
    exam_date: date
    exam_time: Optional[str] = None
    description: Optional[str] = None
    importance: int = 3


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    subject_id: Optional[int] = None
    exam_date: Optional[date] = None
    exam_time: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[int] = None


class ExamOut(BaseModel):
    id: int
    name: str
    subject_id: Optional[int]
    subject_name: Optional[str] = None
    exam_date: date
    exam_time: Optional[str]
    description: Optional[str]
    importance: int
    days_remaining: Optional[int] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------- Resources ---
class ResourceCreate(BaseModel):
    title: str
    subject_id: Optional[int] = None
    grade: Optional[str] = None
    chapter: Optional[str] = None
    url: str
    description: Optional[str] = None
    resource_type: str = "لینک خارجی"
    is_downloadable: bool = False


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    subject_id: Optional[int] = None
    grade: Optional[str] = None
    chapter: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    is_downloadable: Optional[bool] = None


class ResourceOut(BaseModel):
    id: int
    title: str
    subject_id: Optional[int]
    subject_name: Optional[str] = None
    grade: Optional[str]
    chapter: Optional[str]
    url: str
    description: Optional[str]
    resource_type: str
    is_downloadable: bool

    class Config:
        from_attributes = True


# --------------------------------------------------------------- Messages ---
class DailyMessageCreate(BaseModel):
    text: str
    category: str = "انگیزشی"
    is_enabled: bool = True


class DailyMessageUpdate(BaseModel):
    text: Optional[str] = None
    category: Optional[str] = None
    is_enabled: Optional[bool] = None


class DailyMessageOut(BaseModel):
    id: int
    text: str
    category: str
    is_enabled: bool

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ Chat ---
class ChatMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------- Telegram ---
class TelegramSettingsUpdate(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    is_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
    timezone: Optional[str] = None
    daily_reminder_enabled: Optional[bool] = None
    exam_reminder_enabled: Optional[bool] = None
    motivational_reminder_enabled: Optional[bool] = None
    cycle_notifications_enabled: Optional[bool] = None


class TelegramSettingsOut(BaseModel):
    bot_token_set: bool
    chat_id: Optional[str]
    is_enabled: bool
    reminder_time: str
    timezone: str
    daily_reminder_enabled: bool
    exam_reminder_enabled: bool
    motivational_reminder_enabled: bool
    cycle_notifications_enabled: bool


# ----------------------------------------------------------------- Cycle ---
class CycleEntryCreate(BaseModel):
    start_date: date
    cycle_length_days: int = 28
    period_length_days: int = 6
    notes: Optional[str] = None


class CycleEntryOut(BaseModel):
    id: int
    start_date: date
    cycle_length_days: int
    period_length_days: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class CyclePredictionOut(BaseModel):
    last_start_date: Optional[date]
    estimated_next_start: Optional[date]
    estimated_fertile_window_start: Optional[date]
    estimated_fertile_window_end: Optional[date]
    average_cycle_length: Optional[float]
    disclaimer: str = "این تخمین‌ها صرفاً جنبه اطلاعاتی دارند و جایگزین نظر پزشک نیستند."


# ------------------------------------------------------------------ Admin ---
class AdminDashboardOut(BaseModel):
    today_tasks_total: int
    today_tasks_completed: int
    upcoming_exams: int
    telegram_enabled: bool
    resources_count: int
    active_subjects: int
    recent_activity: List[dict]


class ActivityLogOut(BaseModel):
    id: int
    username: Optional[str]
    action: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
