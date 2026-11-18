from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from plant_tracker import timeutil as t

NY = ZoneInfo("America/New_York")


def test_local_date_crosses_midnight():
    # 02:30 UTC on Nov 11 is 21:30 on Nov 10 in New York
    dt = datetime(2026, 11, 11, 2, 30, tzinfo=timezone.utc)
    assert t.local_date(dt, NY) == date(2026, 11, 10)


def test_iso_round_trip_is_utc():
    dt = datetime(2026, 11, 10, 9, 0, tzinfo=NY)
    s = t.to_iso(dt)
    assert s.endswith("+00:00")
    assert t.from_iso(s) == dt


def test_parse_local_datetime_uses_household_zone():
    parsed = t.parse_local_datetime("2026-11-10T08:30", NY)
    assert parsed == datetime(2026, 11, 10, 13, 30, tzinfo=timezone.utc)


def test_parse_local_datetime_rejects_garbage():
    with pytest.raises(ValueError):
        t.parse_local_datetime("not a date", NY)


def test_is_future_allows_small_grace():
    now = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
    assert not t.is_future(now.replace(second=30), now)
    assert t.is_future(now.replace(minute=5), now)


def test_format_when():
    now = datetime(2026, 11, 10, 15, 0, tzinfo=NY)
    assert t.format_when(datetime(2026, 11, 10, 9, 15, tzinfo=NY), now, NY) == "today 09:15"
    assert t.format_when(datetime(2026, 11, 9, 18, 0, tzinfo=NY), now, NY) == "yesterday 18:00"
    assert t.format_when(datetime(2026, 11, 3, 9, 15, tzinfo=NY), now, NY) == "Tue Nov 3 09:15"


def test_format_date():
    today = date(2026, 11, 10)
    assert t.format_date(today, today) == "today"
    assert t.format_date(date(2026, 11, 11), today) == "tomorrow"
    assert t.format_date(date(2026, 11, 17), today) == "Tue Nov 17"
