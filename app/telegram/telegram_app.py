"""
python-telegram-bot Application: command handlers + free-text handler.

Run only from worker.py (separate Railway service / process), using long
polling so reminders and Q&A keep working even when the website is closed.

IMPORTANT TECHNICAL NOTE:
Telegram's Bot API only recognizes "/command" as a bot_command entity when
it matches [a-zA-Z0-9_]{1,32} -- non-Latin scripts (Persian) are NOT parsed
as command entities by Telegram's servers. So Persian "commands" like
"/امروز" arrive as plain text messages, not as CommandHandler-matched
commands. We handle them here by matching the raw text (with or without a
leading slash) in a single text handler, which also powers free-text
Persian questions such as "امتحان بعدی من کیه؟".
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.database import SessionLocal
from app.telegram.bot import (
    answer_free_text_question,
    build_next_exam_text,
    build_resources_text,
    build_status_text,
    build_today_plan_text,
)

logger = logging.getLogger("telegram_bot.app")

WELCOME_TEXT = (
    "سلام! 🌱 من دستیار برنامه مطالعاتی مهرسا هستم.\n\n"
    "دستورات:\n"
    "/امروز - برنامه امروز\n"
    "/برنامه - برنامه امروز\n"
    "/امتحان - آزمون بعدی\n"
    "/کتاب - آخرین منابع\n"
    "/یادآوری - وضعیت امروز\n"
    "/وضعیت - وضعیت پیشرفت امروز\n\n"
    "همچنین می‌تونی سوالاتی مثل «امتحان بعدی من کیه؟» یا «امروز چه روزیه؟» بپرسی."
)

# Persian pseudo-commands, matched against the raw message text
# (leading "/" is stripped before comparison).
_PERSIAN_COMMANDS = {
    "امروز": lambda db: build_today_plan_text(db),
    "برنامه": lambda db: build_today_plan_text(db),
    "امتحان": lambda db: build_next_exam_text(db),
    "کتاب": lambda db: build_resources_text(db),
    "یادآوری": lambda db: build_status_text(db),
    "وضعیت": lambda db: build_status_text(db),
}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = (update.message.text or "").strip()
    key = raw[1:].strip() if raw.startswith("/") else raw

    with SessionLocal() as db:
        handler = _PERSIAN_COMMANDS.get(key)
        if handler:
            await update.message.reply_text(handler(db))
            return

        answer = answer_free_text_question(db, raw)
        if answer:
            await update.message.reply_text(answer)
            return

    if raw.startswith("/"):
        await update.message.reply_text(
            "این دستور رو نمی‌شناسم 🙏 از /امروز /امتحان /کتاب /وضعیت استفاده کن."
        )
    else:
        await update.message.reply_text(
            "متوجه سوالت نشدم 🙏 می‌تونی از دستورات /امروز /امتحان /کتاب /وضعیت استفاده کنی."
        )


def build_application(bot_token: str) -> Application:
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    # Single catch-all text handler: covers both Persian slash-commands
    # (which Telegram does NOT parse as command entities) and free-text
    # Persian questions.
    application.add_handler(MessageHandler(filters.TEXT, handle_text))

    return application
