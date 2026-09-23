"""
Backup service.

Produces a JSON export of all application data (excluding password hashes
and Telegram bot token) so Ali can back up the site's content from within
the admin panel and download it. Also supports restoring from such a
backup file.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    ChatMessage,
    CycleEntry,
    DailyMessage,
    Exam,
    NextDaySelection,
    Resource,
    StudyTask,
    Subject,
    SystemSetting,
    WeeklyPlan,
)

EXPORTABLE_MODELS = {
    "subjects": Subject,
    "study_tasks": StudyTask,
    "next_day_selections": NextDaySelection,
    "weekly_plans": WeeklyPlan,
    "exams": Exam,
    "resources": Resource,
    "daily_messages": DailyMessage,
    "chat_messages": ChatMessage,
    "cycle_entries": CycleEntry,
    "system_settings": SystemSetting,
}


def _row_to_dict(row) -> Dict[str, Any]:
    data = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif hasattr(value, "isoformat"):  # date
            value = value.isoformat()
        elif hasattr(value, "value"):  # Enum
            value = value.value
        data[column.name] = value
    return data


def create_backup(db: Session, include_cycle_data: bool = False) -> Dict[str, Any]:
    export: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app": "mehrsa-study-planner",
        "version": 1,
        "tables": {},
    }
    for table_name, model in EXPORTABLE_MODELS.items():
        if table_name == "cycle_entries" and not include_cycle_data:
            continue
        rows = db.execute(select(model)).scalars().all()
        export["tables"][table_name] = [_row_to_dict(r) for r in rows]
    return export


def save_backup_to_disk(db: Session, include_cycle_data: bool = False) -> str:
    os.makedirs(settings.backup_dir, exist_ok=True)
    payload = create_backup(db, include_cycle_data=include_cycle_data)
    filename = f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    filepath = os.path.join(settings.backup_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return filepath
