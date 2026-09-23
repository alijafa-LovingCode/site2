from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.database import get_db
from app.models import TelegramSettings, User
from app.schemas import TelegramSettingsOut, TelegramSettingsUpdate
from app.services.activity_log import log_activity
from app.telegram.bot import send_telegram_message

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


def _get_or_create_settings(db: Session) -> TelegramSettings:
    cfg = db.execute(select(TelegramSettings)).scalars().first()
    if not cfg:
        cfg = TelegramSettings()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _to_out(cfg: TelegramSettings) -> TelegramSettingsOut:
    return TelegramSettingsOut(
        bot_token_set=bool(cfg.bot_token),
        chat_id=cfg.chat_id,
        is_enabled=cfg.is_enabled,
        reminder_time=cfg.reminder_time,
        timezone=cfg.timezone,
        daily_reminder_enabled=cfg.daily_reminder_enabled,
        exam_reminder_enabled=cfg.exam_reminder_enabled,
        motivational_reminder_enabled=cfg.motivational_reminder_enabled,
        cycle_notifications_enabled=cfg.cycle_notifications_enabled,
    )


@router.get("/settings", response_model=TelegramSettingsOut)
def get_settings_route(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    cfg = _get_or_create_settings(db)
    return _to_out(cfg)


@router.put("/settings", response_model=TelegramSettingsOut)
def update_settings(payload: TelegramSettingsUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    cfg = _get_or_create_settings(db)
    data = payload.model_dump(exclude_unset=True)
    # bot_token is never returned to the frontend; only overwritten when a
    # new non-empty value is explicitly submitted.
    for field, value in data.items():
        if field == "bot_token" and not value:
            continue
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    log_activity(db, admin, "telegram_settings_updated")
    return _to_out(cfg)


@router.post("/test-send")
async def test_send(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    ok = await send_telegram_message("✅ این یک پیام آزمایشی از برنامه مطالعاتی مهرساست.", db=db)
    log_activity(db, admin, "telegram_test_send", details="success" if ok else "failed")
    return {"success": ok}
