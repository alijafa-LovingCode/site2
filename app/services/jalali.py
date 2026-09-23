"""
Persian (Jalali) calendar helpers.

Storage is always Gregorian/UTC (via `date`/`datetime`). This module only
converts values for *display* purposes, keeping scheduling and storage
reliable while giving Mehrsa a fully Persian-dated UI.
"""
from __future__ import annotations

from datetime import date, datetime

import jdatetime

PERSIAN_WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

# Python's date.weekday(): Monday=0 ... Sunday=6
# Persian week starts Saturday. Map Python weekday -> Persian weekday index.
_PY_WEEKDAY_TO_FA_INDEX = {
    5: 0,  # Saturday
    6: 1,  # Sunday
    0: 2,  # Monday
    1: 3,  # Tuesday
    2: 4,  # Wednesday
    3: 5,  # Thursday
    4: 6,  # Friday
}

PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def to_fa_digits(value) -> str:
    s = str(value)
    return "".join(_FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in s)


def gregorian_to_jalali_str(d: date) -> str:
    jd = jdatetime.date.fromgregorian(date=d)
    return to_fa_digits(f"{jd.year}/{jd.month:02d}/{jd.day:02d}")


def gregorian_to_jalali_long(d: date) -> str:
    jd = jdatetime.date.fromgregorian(date=d)
    weekday_fa = PERSIAN_WEEKDAYS[_PY_WEEKDAY_TO_FA_INDEX[d.weekday()]]
    month_fa = PERSIAN_MONTHS[jd.month - 1]
    return f"{weekday_fa} {to_fa_digits(jd.day)} {month_fa} {to_fa_digits(jd.year)}"


def persian_weekday_name(d: date) -> str:
    return PERSIAN_WEEKDAYS[_PY_WEEKDAY_TO_FA_INDEX[d.weekday()]]


def today_local(tz_name: str = "Asia/Tehran") -> date:
    try:
        import pytz

        tz = pytz.timezone(tz_name)
        return datetime.now(tz).date()
    except Exception:
        return date.today()
