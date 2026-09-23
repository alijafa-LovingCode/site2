from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config import settings
from app.models import RoleEnum, TelegramSettings, User
from app.services.messages_seed import seed_daily_messages, seed_subjects

logger = logging.getLogger("startup")


def seed_users(db: Session) -> None:
    ali = db.execute(select(User).where(User.username == "ali")).scalar_one_or_none()
    if not ali:
        ali = User(
            username="ali",
            display_name="علی",
            role=RoleEnum.ADMIN,
            password_hash=hash_password(settings.admin_password),
        )
        db.add(ali)
        logger.info("Seeded initial admin user 'ali'")

    mehrsa = db.execute(select(User).where(User.username == "mehrsa")).scalar_one_or_none()
    if not mehrsa:
        mehrsa = User(
            username="mehrsa",
            display_name="مهرسا",
            role=RoleEnum.STUDENT,
            password_hash=hash_password(settings.student_password),
        )
        db.add(mehrsa)
        logger.info("Seeded initial student user 'mehrsa'")

    db.commit()


def seed_telegram_settings(db: Session) -> None:
    existing = db.execute(select(TelegramSettings)).scalars().first()
    if existing:
        return
    cfg = TelegramSettings(
        bot_token=settings.telegram_bot_token or None,
        chat_id=settings.telegram_chat_id or None,
        is_enabled=settings.telegram_enabled,
        timezone=settings.telegram_timezone,
    )
    db.add(cfg)
    db.commit()
    logger.info("Seeded initial Telegram settings")


def run_startup_seed(db: Session) -> None:
    seed_users(db)
    seed_subjects(db)
    seed_daily_messages(db)
    seed_telegram_settings(db)
