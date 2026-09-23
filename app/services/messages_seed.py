from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMessage, MessageCategoryEnum, MessageDelivery

DEFAULT_SUBJECTS = [
    ("ریاضی", 1, 5, "#EF5350"),
    ("فیزیک", 2, 4, "#42A5F5"),
    ("شیمی", 2, 4, "#66BB6A"),
    ("زیست", 2, 3, "#26A69A"),
    ("ادبیات", 3, 2, "#AB47BC"),
    ("عربی", 3, 3, "#FFA726"),
    ("دینی", 4, 2, "#8D6E63"),
    ("زبان", 3, 2, "#5C6BC0"),
]

DEFAULT_MESSAGES = [
    ("امروز هم یه قدم به هدفت نزدیک‌تر شدی، مهرسا 🌱", MessageCategoryEnum.MOTIVATIONAL),
    ("هر ساعت مطالعه امروز، اعتماد به نفس فرداته 💪", MessageCategoryEnum.STUDY),
    ("لازم نیست عالی باشی، فقط ادامه بده 🌸", MessageCategoryEnum.MOTIVATIONAL),
    ("یه نفس عمیق بکش، همه چی مرتبه 🍃", MessageCategoryEnum.CALM),
    ("بعد از این همه تلاش، استراحت هم حقته 🌙", MessageCategoryEnum.REST),
    ("آزمون فقط یه ایستگاهه، نه خط پایان 🚋", MessageCategoryEnum.EXAM),
    ("امروز رو با انرژی مثبت شروع کن ☀️", MessageCategoryEnum.DAILY_POSITIVE),
    ("هر فصل که تموم می‌کنی، یه پیروزی کوچیکه 🏆", MessageCategoryEnum.STUDY),
    ("نگران نباش، قدم‌به‌قدم پیش می‌ری 🐾", MessageCategoryEnum.CALM),
    ("تو خیلی بیشتر از چیزی که فکر می‌کنی توانایی داری ✨", MessageCategoryEnum.MOTIVATIONAL),
    ("یه لیوان آب بخور و برنامه امروزت رو شروع کن 💧", MessageCategoryEnum.DAILY_POSITIVE),
    ("قبل از آزمون، فقط مرور کن نه استرس 📘", MessageCategoryEnum.EXAM),
    ("هر روز بهتر از دیروز، همینم کافیه 🌼", MessageCategoryEnum.MOTIVATIONAL),
    ("۱۰ دقیقه استراحت بین درس‌ها، تمرکزت رو بیشتر می‌کنه ⏳", MessageCategoryEnum.REST),
    ("مطالعه منظم از مطالعه فشرده مؤثرتره 📚", MessageCategoryEnum.STUDY),
    ("امروز چالش‌های کوچیک، فردا موفقیت‌های بزرگ می‌شن 🌟", MessageCategoryEnum.MOTIVATIONAL),
    ("اگه خسته‌ای، یکم قدم بزن و برگرد 🚶‍♀️", MessageCategoryEnum.REST),
    ("آرامشت رو با هیچی عوض نکن، حتی نمره 🕊️", MessageCategoryEnum.CALM),
    ("قبل خواب، برنامه فردا رو مرور کن 🌜", MessageCategoryEnum.STUDY),
    ("همین که تلاش می‌کنی افتخارآفرینه 🎗️", MessageCategoryEnum.MOTIVATIONAL),
    ("آزمون بعدی نزدیکه، ولی تو آماده‌تر از قبلی 📝", MessageCategoryEnum.EXAM),
    ("خودتو با دیروزت مقایسه کن نه با بقیه 🌱", MessageCategoryEnum.MOTIVATIONAL),
    ("نفس بکش، لبخند بزن، ادامه بده 😊", MessageCategoryEnum.DAILY_POSITIVE),
    ("هر درسی که امروز خوندی، فردا سبک‌ترت می‌کنه 🎒", MessageCategoryEnum.STUDY),
    ("گاهی یه وقفه کوتاه، بهترین تصمیمه ☕", MessageCategoryEnum.REST),
    ("تو لایق نتیجه تلاش‌هاتی، صبور باش 🌷", MessageCategoryEnum.MOTIVATIONAL),
    ("امروز رو ساده و منظم شروع کن، بدون عجله 🕰️", MessageCategoryEnum.CALM),
    ("جمع‌بندی فصل‌های قبلی رو فراموش نکن 📖", MessageCategoryEnum.EXAM),
    ("هر روز یه فرصت تازه‌ست برای بهتر شدن 🌅", MessageCategoryEnum.DAILY_POSITIVE),
    ("مهرسا جان، بهت افتخار می‌کنیم 💖", MessageCategoryEnum.MOTIVATIONAL),
]


def seed_subjects(db: Session) -> None:
    from app.models import Subject

    existing = db.execute(select(Subject.name)).scalars().all()
    existing_set = set(existing)
    for name, priority, difficulty, color in DEFAULT_SUBJECTS:
        if name not in existing_set:
            db.add(Subject(name=name, priority=priority, difficulty=difficulty, color=color))
    db.commit()


def seed_daily_messages(db: Session) -> None:
    existing_count = db.execute(select(DailyMessage.id)).first()
    if existing_count:
        return
    for text, category in DEFAULT_MESSAGES:
        db.add(DailyMessage(text=text, category=category))
    db.commit()


def get_message_for_date(db: Session, target_date: date) -> Optional[DailyMessage]:
    """Return the message assigned to `target_date`, creating a
    non-repeating assignment if one doesn't exist yet. Cycles through the
    enabled message pool without repeating until it's exhausted."""
    existing_delivery = db.execute(
        select(MessageDelivery).where(MessageDelivery.delivered_date == target_date)
    ).scalar_one_or_none()
    if existing_delivery:
        return db.get(DailyMessage, existing_delivery.message_id)

    enabled_messages = db.execute(
        select(DailyMessage).where(DailyMessage.is_enabled.is_(True)).order_by(DailyMessage.id)
    ).scalars().all()
    if not enabled_messages:
        return None

    pool_size = len(enabled_messages)

    # How many deliveries have happened in the current cycle window?
    cycle_start_candidate = target_date - timedelta(days=pool_size - 1)
    recent_deliveries = db.execute(
        select(MessageDelivery.message_id)
        .where(MessageDelivery.delivered_date >= cycle_start_candidate, MessageDelivery.delivered_date < target_date)
        .order_by(MessageDelivery.delivered_date)
    ).scalars().all()

    used_ids = set(recent_deliveries)
    remaining = [m for m in enabled_messages if m.id not in used_ids]
    if not remaining:
        remaining = enabled_messages  # pool exhausted -> start a fresh cycle

    # Deterministic pick based on ordinal day count, so re-computation is stable
    day_index = target_date.toordinal()
    chosen = remaining[day_index % len(remaining)]

    db.add(MessageDelivery(message_id=chosen.id, delivered_date=target_date))
    db.commit()
    return chosen
