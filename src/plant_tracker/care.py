"""Plant care status rules (data-model.md "Derived state").

Everything here is a pure function of a plant's schedule, its care events, and the current time,
so the rules can be unit-tested with fixed clocks (Constitution Principle V). Nothing in this
module changes state: only recorded events do (Constitution Principle II).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, tzinfo
from typing import Iterable

from .timeutil import local_date, plural

# Care event kinds (data-model.md care_event.kind)
WATERED = "watered"
MOVED_OUTSIDE = "moved_outside"
BROUGHT_INSIDE = "brought_inside"
EVENT_KINDS = (WATERED, MOVED_OUTSIDE, BROUGHT_INSIDE)
EVENT_LABELS = {
    WATERED: "Watered",
    MOVED_OUTSIDE: "Moved outside",
    BROUGHT_INSIDE: "Brought inside",
}

# Watering states
NEVER = "never"
OK = "ok"
DUE_TODAY = "due_today"
OVERDUE = "overdue"


@dataclass(frozen=True)
class Event:
    kind: str
    occurred_at: datetime  # aware UTC
    member_name: str
    id: int | None = None
    member_id: int | None = None

    @property
    def label(self) -> str:
        return EVENT_LABELS[self.kind]


def latest(events: Iterable[Event], *kinds: str) -> Event | None:
    """Most recent event of the given kinds by when it happened (ties: later id wins)."""
    matching = [e for e in events if e.kind in kinds]
    if not matching:
        return None
    return max(matching, key=lambda e: (e.occurred_at, e.id or 0))


# --------------------------------------------------------------------------- watering (G2)


@dataclass(frozen=True)
class WateringStatus:
    state: str
    last: Event | None
    next_due: date | None
    days_overdue: int = 0
    days_until_due: int = 0

    @property
    def label(self) -> str:
        if self.state == NEVER:
            return "Never watered"
        if self.state == DUE_TODAY:
            return "Due today"
        if self.state == OVERDUE:
            return f"Overdue by {plural(self.days_overdue, 'day')}"
        return f"Water in {plural(self.days_until_due, 'day')}"

    @property
    def needs_water(self) -> bool:
        return self.state in (NEVER, DUE_TODAY, OVERDUE)


def watering_status(
    interval_days: int, events: Iterable[Event], now: datetime, tz: tzinfo | None
) -> WateringStatus:
    """FR-009-FR-011: last watered, next due (calendar days, local time), and state."""
    last = latest(events, WATERED)
    if last is None:
        return WateringStatus(state=NEVER, last=None, next_due=None)

    today = local_date(now, tz)
    next_due = local_date(last.occurred_at, tz) + timedelta(days=interval_days)
    if today > next_due:
        return WateringStatus(OVERDUE, last, next_due, days_overdue=(today - next_due).days)
    if today == next_due:
        return WateringStatus(DUE_TODAY, last, next_due)
    return WateringStatus(OK, last, next_due, days_until_due=(next_due - today).days)
