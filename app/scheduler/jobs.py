"""
Background scheduled jobs, run by the worker process (worker.py).

Uses APScheduler with a cron-style trigger driven by the TelegramSettings
row stored in the database (reminder_time, timezone), so Ali can change
the reminder time from the admin panel without redeploying.

Jobs:
  - daily_reminder_job: sends today's plan + motivational message
  - exam_reminder_job: sends exam countdown alerts (0/1/3/7 days out)
  - chat_cleanup_job: deletes chat messages older than CHAT_RETENTION_HOURS
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import delete, select

from app.config import settings
from app.database import SessionLocal
from app.models import ChatMessage
from app.telegram.bot import (
    build_exam_countdown_reminder,
    build_reminder_text,
    get_telegram_settings,
    send_telegram_message,
)

logger = logging.getLogger("scheduler")


async def daily_reminder_job() -> None:
    with SessionLocal() as db:
        cfg = get_telegram_settings(db)
        if not cfg or not cfg.is_enabled or not cfg.daily_reminder_enabled:
            return
        text = build_reminder_text(db)
        sent = await send_telegram_message(text, db=db)
        if sent:
            logger.info("Daily reminder sent")
        else:
            logger.warning("Daily reminder could not be sent")


async def exam_reminder_job() -> None:
    with SessionLocal() as db:
        cfg = get_telegram_settings(db)
        if not cfg or not cfg.is_enabled or not cfg.exam_reminder_enabled:
            return
        text = build_exam_countdown_reminder(db)
        if not text:
            return
        sent = await send_telegram_message(text, db=db)
        if sent:
            logger.info("Exam reminder sent")


async def motivational_job() -> None:
    with SessionLocal() as db:
        cfg = get_telegram_settings(db)
        if not cfg or not cfg.is_enabled or not cfg.motivational_reminder_enabled:
            return
        from app.services.jalali import today_local
        from app.services.messages_seed import get_message_for_date

        today = today_local(settings.telegram_timezone)
        msg = get_message_for_date(db, today)
        if not msg:
            return
        await send_telegram_message(msg.text, db=db)


async def chat_cleanup_job() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.chat_retention_hours)
    with SessionLocal() as db:
        result = db.execute(delete(ChatMessage).where(ChatMessage.created_at < cutoff))
        db.commit()
        if result.rowcount:
            logger.info("Chat cleanup removed %s old messages", result.rowcount)


def _get_reminder_time_parts(db) -> tuple[int, int, str]:
    cfg = get_telegram_settings(db)
    if not cfg:
        return 8, 0, settings.telegram_timezone
    try:
        hour, minute = cfg.reminder_time.split(":")
        return int(hour), int(minute), cfg.timezone or settings.telegram_timezone
    except Exception:
        return 8, 0, settings.telegram_timezone


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.telegram_timezone)

    with SessionLocal() as db:
        hour, minute, tz = _get_reminder_time_parts(db)

    scheduler.add_job(
        daily_reminder_job,
        CronTrigger(hour=hour, minute=minute, timezone=tz),
        id="daily_reminder",
        replace_existing=True,
    )
    # Exam countdown + motivational + status checks run periodically
    scheduler.add_job(
        exam_reminder_job,
        CronTrigger(hour=9, minute=0, timezone=tz),
        id="exam_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        motivational_job,
        CronTrigger(hour=12, minute=0, timezone=tz),
        id="motivational",
        replace_existing=True,
    )
    scheduler.add_job(
        chat_cleanup_job,
        CronTrigger(minute="*/30"),
        id="chat_cleanup",
        replace_existing=True,
    )
    return scheduler
