"""Time helpers. Stored times are UTC ISO strings; rules and display use household local time.

`tz=None` means "the server's system time zone" (research.md R-4).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo

# Allow a small clock difference between a phone and the server when checking "not in the future".
FUTURE_GRACE = timedelta(minutes=1)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def from_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_local(dt: datetime, tz: tzinfo | None) -> datetime:
    return dt.astimezone(tz) if tz is not None else dt.astimezone()


def local_date(dt: datetime, tz: tzinfo | None) -> date:
    return to_local(dt, tz).date()


def parse_local_datetime(value: str, tz: tzinfo | None) -> datetime:
    """Parse an HTML datetime-local value ("2026-11-10T08:30") in local time; return aware UTC."""
    try:
        naive = datetime.fromisoformat(value.strip())
    except ValueError:
        raise ValueError("That date and time could not be read.") from None
    if naive.tzinfo is None:
        local = naive.replace(tzinfo=tz) if tz is not None else naive.astimezone()
    else:
        local = naive
    return local.astimezone(timezone.utc)


def is_future(dt: datetime, now: datetime) -> bool:
    return dt > now + FUTURE_GRACE


def datetime_local_value(dt: datetime, tz: tzinfo | None) -> str:
    """Format for an <input type="datetime-local"> value."""
    return to_local(dt, tz).strftime("%Y-%m-%dT%H:%M")


def format_time(dt: datetime, tz: tzinfo | None) -> str:
    return to_local(dt, tz).strftime("%H:%M")


def format_when(dt: datetime, now: datetime, tz: tzinfo | None) -> str:
    """Friendly local timestamp: 'today 09:15', 'yesterday 18:00', 'Mon Nov 3 09:15'."""
    local = to_local(dt, tz)
    days = (local_date(now, tz) - local.date()).days
    hhmm = local.strftime("%H:%M")
    if days == 0:
        return f"today {hhmm}"
    if days == 1:
        return f"yesterday {hhmm}"
    if days == -1:
        return f"tomorrow {hhmm}"
    return f"{local.strftime('%a %b')} {local.day} {hhmm}"


def format_date(d: date, today: date) -> str:
    """Friendly local date: 'today', 'tomorrow', 'yesterday', 'Mon Nov 17'."""
    days = (d - today).days
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    if days == -1:
        return "yesterday"
    return f"{d.strftime('%a %b')} {d.day}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"
