"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-23

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_enum = sa.Enum("ADMIN", "STUDENT", name="roleenum")
resource_type_enum = sa.Enum("PDF", "کتاب", "جزوه", "لینک خارجی", "ویدئو", name="resourcetypeenum")
message_category_enum = sa.Enum(
    "انگیزشی", "مطالعه", "آزمون", "آرامش", "استراحت", "مثبت روزانه", name="messagecategoryenum"
)
sender_enum = sa.Enum("ALI", "MEHRSA", name="senderenum")


def upgrade() -> None:
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    resource_type_enum.create(bind, checkfirst=True)
    message_category_enum.create(bind, checkfirst=True)
    sender_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("priority", sa.Integer(), server_default="3"),
        sa.Column("difficulty", sa.Integer(), server_default="3"),
        sa.Column("color", sa.String(20), server_default="#6C63FF"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "study_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("chapter", sa.String(200), nullable=True),
        sa.Column("task", sa.String(300), nullable=True),
        sa.Column("start_time", sa.String(5), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), server_default="60"),
        sa.Column("break_minutes", sa.Integer(), server_default="10"),
        sa.Column("priority", sa.Integer(), server_default="3"),
        sa.Column("exam_relevant", sa.Boolean(), server_default=sa.false()),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.false()),
        sa.Column("is_ai_generated", sa.Boolean(), server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_study_tasks_date", "study_tasks", ["date"])

    op.create_table(
        "next_day_selections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("date", "subject_id", name="uq_nextday_date_subject"),
    )
    op.create_index("ix_next_day_selections_date", "next_day_selections", ["date"])

    op.create_table(
        "weekly_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("week_start_date", sa.Date(), nullable=False, unique=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_weekly_plans_week_start_date", "weekly_plans", ["week_start_date"])

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("exam_time", sa.String(5), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("importance", sa.Integer(), server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_exams_exam_date", "exams", ["exam_date"])

    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("grade", sa.String(50), nullable=True),
        sa.Column("chapter", sa.String(200), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", resource_type_enum, server_default="لینک خارجی"),
        sa.Column("is_downloadable", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "daily_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", message_category_enum, server_default="انگیزشی"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "message_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("daily_messages.id", ondelete="CASCADE")),
        sa.Column("delivered_date", sa.Date(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_message_deliveries_delivered_date", "message_deliveries", ["delivered_date"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sender", sender_enum, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])

    op.create_table(
        "telegram_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bot_token", sa.String(255), nullable=True),
        sa.Column("chat_id", sa.String(100), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.false()),
        sa.Column("reminder_time", sa.String(5), server_default="08:00"),
        sa.Column("timezone", sa.String(50), server_default="Asia/Tehran"),
        sa.Column("daily_reminder_enabled", sa.Boolean(), server_default=sa.true()),
        sa.Column("exam_reminder_enabled", sa.Boolean(), server_default=sa.true()),
        sa.Column("motivational_reminder_enabled", sa.Boolean(), server_default=sa.true()),
        sa.Column("cycle_notifications_enabled", sa.Boolean(), server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ask_next_day_subjects_time", sa.String(5), server_default="20:00"),
        sa.Column("daily_completion_check_time", sa.String(5), server_default="21:30"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cycle_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("cycle_length_days", sa.Integer(), server_default="28"),
        sa.Column("period_length_days", sa.Integer(), server_default="6"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("username", sa.String(50), nullable=True),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("system_settings")
    op.drop_table("cycle_entries")
    op.drop_table("notification_settings")
    op.drop_table("telegram_settings")
    op.drop_table("chat_messages")
    op.drop_table("message_deliveries")
    op.drop_table("daily_messages")
    op.drop_table("resources")
    op.drop_table("exams")
    op.drop_table("weekly_plans")
    op.drop_table("next_day_selections")
    op.drop_table("study_tasks")
    op.drop_table("subjects")
    op.drop_table("users")

    bind = op.get_bind()
    sender_enum.drop(bind, checkfirst=True)
    message_category_enum.drop(bind, checkfirst=True)
    resource_type_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)
