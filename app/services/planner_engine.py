"""
Deterministic study planning engine.

This is the built-in planner that runs with or without an AI provider
configured. It generates a concrete list of StudyTask records for a given
date, based on:

  1. Subjects Mehrsa selected for that day (next-day selection)
  2. Upcoming exams (closer exam -> higher weight)
  3. Subject priority / difficulty
  4. Unfinished tasks carried over from previous days
  5. A configurable daily study-time budget
  6. Reasonable breaks between tasks

The output is NOT random: the same inputs always produce the same plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exam, StudyTask, Subject

DEFAULT_DAILY_BUDGET_MINUTES = 240  # 4 hours default study budget per day
MIN_TASK_MINUTES = 30
MAX_TASK_MINUTES = 90
BREAK_MINUTES = 10
REVIEW_BLOCK_MINUTES = 30


@dataclass
class PlannedItem:
    subject_id: int
    subject_name: str
    chapter: Optional[str]
    task: str
    duration_minutes: int
    break_minutes: int
    priority: int
    exam_relevant: bool
    notes: Optional[str] = None


def _exam_weight(days_remaining: int) -> float:
    """Closer exams get a bigger weight. Never negative."""
    if days_remaining <= 0:
        return 3.0
    if days_remaining <= 2:
        return 2.5
    if days_remaining <= 5:
        return 2.0
    if days_remaining <= 10:
        return 1.5
    return 1.0


def _score_subject(
    subject: Subject,
    target_date: date,
    exams_by_subject: dict[int, Exam],
    unfinished_count: int,
) -> float:
    # Lower `priority` number == more important (1 highest .. 5 lowest)
    priority_score = (6 - subject.priority)
    difficulty_score = subject.difficulty * 0.5

    exam_score = 0.0
    exam = exams_by_subject.get(subject.id)
    if exam:
        days_remaining = (exam.exam_date - target_date).days
        exam_score = _exam_weight(days_remaining) * (6 - exam.importance)

    unfinished_score = min(unfinished_count, 3) * 0.75

    return priority_score + difficulty_score + exam_score + unfinished_score


def generate_daily_plan(
    db: Session,
    target_date: date,
    subject_ids: List[int],
    daily_budget_minutes: int = DEFAULT_DAILY_BUDGET_MINUTES,
) -> List[PlannedItem]:
    """Build a study plan for `target_date` using only the given subjects.

    This function is pure/deterministic given the same database state.
    """
    if not subject_ids:
        return []

    subjects = db.execute(
        select(Subject).where(Subject.id.in_(subject_ids), Subject.is_active.is_(True))
    ).scalars().all()
    if not subjects:
        return []

    # Nearest upcoming exam per subject (only future/today exams matter)
    exams = db.execute(
        select(Exam).where(Exam.subject_id.in_(subject_ids), Exam.exam_date >= target_date)
    ).scalars().all()
    exams_by_subject: dict[int, Exam] = {}
    for exam in exams:
        current = exams_by_subject.get(exam.subject_id)
        if current is None or exam.exam_date < current.exam_date:
            exams_by_subject[exam.subject_id] = exam

    # Count unfinished tasks from the last 7 days for each subject (carry-over signal)
    lookback_start = target_date - timedelta(days=7)
    unfinished_tasks = db.execute(
        select(StudyTask).where(
            StudyTask.subject_id.in_(subject_ids),
            StudyTask.date >= lookback_start,
            StudyTask.date < target_date,
            StudyTask.is_completed.is_(False),
        )
    ).scalars().all()
    unfinished_by_subject: dict[int, int] = {}
    for t in unfinished_tasks:
        unfinished_by_subject[t.subject_id] = unfinished_by_subject.get(t.subject_id, 0) + 1

    scored = sorted(
        subjects,
        key=lambda s: _score_subject(
            s, target_date, exams_by_subject, unfinished_by_subject.get(s.id, 0)
        ),
        reverse=True,
    )

    total_weight = sum(
        max(
            _score_subject(s, target_date, exams_by_subject, unfinished_by_subject.get(s.id, 0)),
            0.1,
        )
        for s in scored
    )

    # Reserve a fixed review block if budget allows and there's more than one subject
    budget = daily_budget_minutes
    reserve_review = len(scored) > 1 and budget > REVIEW_BLOCK_MINUTES + MIN_TASK_MINUTES
    working_budget = budget - REVIEW_BLOCK_MINUTES if reserve_review else budget

    items: List[PlannedItem] = []
    allocated_total = 0
    for subject in scored:
        weight = max(
            _score_subject(subject, target_date, exams_by_subject, unfinished_by_subject.get(subject.id, 0)),
            0.1,
        )
        share = working_budget * (weight / total_weight)
        # Round to nearest 15 minutes, clamp to sane bounds
        duration = int(round(share / 15.0) * 15)
        duration = max(MIN_TASK_MINUTES, min(MAX_TASK_MINUTES, duration))
        allocated_total += duration

        exam = exams_by_subject.get(subject.id)
        exam_relevant = exam is not None
        chapter = None
        task_desc = "مرور و تمرین"
        if exam:
            days_remaining = (exam.exam_date - target_date).days
            task_desc = f"آمادگی آزمون ({to_days_label(days_remaining)})"

        items.append(
            PlannedItem(
                subject_id=subject.id,
                subject_name=subject.name,
                chapter=chapter,
                task=task_desc,
                duration_minutes=duration,
                break_minutes=BREAK_MINUTES,
                priority=subject.priority,
                exam_relevant=exam_relevant,
            )
        )

    # Do not overload the day: if allocation exceeds budget due to rounding,
    # trim from the lowest-priority (last) items first.
    while allocated_total > budget and items:
        last = items[-1]
        reducible = last.duration_minutes - MIN_TASK_MINUTES
        if reducible <= 0:
            items.pop()
            allocated_total = sum(i.duration_minutes for i in items)
            continue
        cut = min(15, reducible)
        last.duration_minutes -= cut
        allocated_total -= cut

    if reserve_review and items:
        items.append(
            PlannedItem(
                subject_id=items[0].subject_id,
                subject_name="مرور کلی",
                chapter=None,
                task="مرور نکات مهم درس‌های امروز",
                duration_minutes=REVIEW_BLOCK_MINUTES,
                break_minutes=0,
                priority=3,
                exam_relevant=False,
                notes="بلوک مرور خودکار",
            )
        )

    return items


def to_days_label(days_remaining: int) -> str:
    if days_remaining <= 0:
        return "امروز"
    if days_remaining == 1:
        return "فردا"
    return f"{days_remaining} روز مانده"


def persist_plan(db: Session, target_date: date, items: List[PlannedItem], overwrite: bool = True) -> List[StudyTask]:
    """Persist generated plan items as StudyTask rows. If overwrite=True,
    any existing AI/engine-generated (non-manual) tasks for that date are
    replaced; manually created tasks are preserved untouched."""
    if overwrite:
        existing = db.execute(
            select(StudyTask).where(StudyTask.date == target_date, StudyTask.is_ai_generated.is_(True))
        ).scalars().all()
        for t in existing:
            db.delete(t)
        db.flush()

    created: List[StudyTask] = []
    for item in items:
        task = StudyTask(
            subject_id=item.subject_id,
            date=target_date,
            chapter=item.chapter,
            task=item.task,
            duration_minutes=item.duration_minutes,
            break_minutes=item.break_minutes,
            priority=item.priority,
            exam_relevant=item.exam_relevant,
            is_ai_generated=True,
            notes=item.notes,
        )
        db.add(task)
        created.append(task)
    db.commit()
    for t in created:
        db.refresh(t)
    return created
