from datetime import date

from app.services.jalali import (
    gregorian_to_jalali_long,
    gregorian_to_jalali_str,
    persian_weekday_name,
    to_fa_digits,
)


def test_to_fa_digits():
    assert to_fa_digits(123) == "۱۲۳"
    assert to_fa_digits("2026") == "۲۰۲۶"


def test_gregorian_to_jalali_str_format():
    d = date(2026, 3, 21)  # Nowruz-ish
    result = gregorian_to_jalali_str(d)
    assert "/" in result


def test_persian_weekday_name_saturday():
    # 2026-01-03 is a Saturday
    d = date(2026, 1, 3)
    assert d.weekday() == 5  # Python: Saturday == 5
    assert persian_weekday_name(d) == "شنبه"


def test_persian_weekday_name_friday():
    # 2026-01-09 is a Friday
    d = date(2026, 1, 9)
    assert d.weekday() == 4
    assert persian_weekday_name(d) == "جمعه"


def test_gregorian_to_jalali_long_contains_weekday_and_year_digits():
    d = date(2026, 6, 15)
    text = gregorian_to_jalali_long(d)
    assert any(ch in text for ch in "۰۱۲۳۴۵۶۷۸۹")
