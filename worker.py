"""
Worker process entrypoint.

Deploy this as a SEPARATE Railway service (start command: `python worker.py`)
alongside the web service. It runs:

  1. The APScheduler background jobs (daily reminder, exam countdown,
     motivational message, chat cleanup) -- see app/scheduler/jobs.py
  2. The Telegram bot long-polling loop -- see app/telegram/telegram_app.py

Both keep running independently of whether anyone has the website open,
satisfying the requirement that Telegram reminders work even when the
site is closed.

If TELEGRAM_BOT_TOKEN is not configured (via env var or later via the
admin panel), the worker still runs the scheduler (useful for chat
cleanup) but skips starting the Telegram polling loop, retrying
periodically in case Ali configures it later from the admin panel.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import TelegramSettings
from app.scheduler.jobs import build_scheduler
from app.services.startup_seed import run_startup_seed
from app.telegram.telegram_app import build_application
from app.utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("worker")

POLL_RETRY_SECONDS = 60


def get_bot_token() -> str | None:
    with SessionLocal() as db:
        cfg = db.execute(select(TelegramSettings)).scalars().first()
        if cfg and cfg.is_enabled and cfg.bot_token:
            return cfg.bot_token
    return None


async def run_telegram_polling() -> None:
    """Waits for a bot token to be configured, then runs polling forever.
    If the token/enabled flag changes, this simple implementation requires
    a worker restart to pick up the change (Railway makes restarts easy;
    the admin panel also surfaces a note about this)."""
    while True:
        token = get_bot_token()
        if not token:
            logger.info("Telegram not configured yet; retrying in %ss", POLL_RETRY_SECONDS)
            await asyncio.sleep(POLL_RETRY_SECONDS)
            continue

        logger.info("Starting Telegram polling...")
        application = build_application(token)
        try:
            async with application:
                await application.start()
                await application.updater.start_polling()
                # Keep this coroutine alive while polling runs
                while True:
                    await asyncio.sleep(3600)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram polling stopped (%s); retrying in %ss", type(exc).__name__, POLL_RETRY_SECONDS)
            await asyncio.sleep(POLL_RETRY_SECONDS)


async def main() -> None:
    logger.info("Worker starting...")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        run_startup_seed(db)

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler started.")

    await run_telegram_polling()


if __name__ == "__main__":
    asyncio.run(main())
