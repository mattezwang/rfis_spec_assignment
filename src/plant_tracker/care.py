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


# --------------------------------------------------------------------------- dashboard (R17-R19)


@dataclass(frozen=True)
class PlantStatus:
    """Everything the dashboard needs to know about one plant."""

    id: int
    name: str
    location: str
    watering: WateringStatus
    sun: object | None = None  # SunStatus, added with User Story 3


# Dashboard groups in urgency order (FR-023, FR-024; research.md R-8)
G_OVERDUE_INSIDE = "overdue_inside"
G_OVERDUE_WATER = "overdue_water"
G_NEVER_WATERED = "never_watered"
G_DUE_TODAY = "due_today"
G_OUTSIDE = "outside"

GROUP_ORDER = (G_OVERDUE_INSIDE, G_OVERDUE_WATER, G_NEVER_WATERED, G_DUE_TODAY, G_OUTSIDE)
GROUP_TITLES = {
    G_OVERDUE_INSIDE: "Overdue to bring inside",
    G_OVERDUE_WATER: "Overdue for water",
    G_NEVER_WATERED: "Never watered",
    G_DUE_TODAY: "Due for water today",
    G_OUTSIDE: "Outside now",
}

ACTION_WATER = "water"
ACTION_INSIDE = "inside"


@dataclass(frozen=True)
class DashboardItem:
    group: str
    plant: PlantStatus
    action: str


@dataclass(frozen=True)
class Group:
    key: str
    title: str
    items: list


def _watering_item(p: PlantStatus) -> tuple | None:
    """(group, sort key within group) for a plant's watering, or None if it needs nothing."""
    w = p.watering
    if w.state == OVERDUE:
        return G_OVERDUE_WATER, (-w.days_overdue, p.name.casefold(), p.id)
    if w.state == NEVER:
        return G_NEVER_WATERED, (p.name.casefold(), p.id)
    if w.state == DUE_TODAY:
        return G_DUE_TODAY, (p.name.casefold(), p.id)
    return None


def dashboard_items(plants: Iterable[PlantStatus]) -> list[DashboardItem]:
    """One item per reason a plant needs attention, most urgent first."""
    keyed = []
    for p in plants:
        watering = _watering_item(p)
        if watering:
            group, key = watering
            keyed.append((GROUP_ORDER.index(group), key, DashboardItem(group, p, ACTION_WATER)))
    keyed.sort(key=lambda t: (t[0], t[1]))
    return [item for _, _, item in keyed]


def group_items(items: list[DashboardItem]) -> list[Group]:
    """Split ordered items into non-empty groups, keeping urgency order."""
    groups = []
    for key in GROUP_ORDER:
        members = [i for i in items if i.group == key]
        if members:
            groups.append(Group(key, GROUP_TITLES[key], members))
    return groups


def next_upcoming(plants: Iterable[PlantStatus]) -> PlantStatus | None:
    """The plant whose next watering comes soonest (for the empty dashboard, FR-026)."""
    upcoming = [p for p in plants if p.watering.state == OK]
    if not upcoming:
        return None
    return min(upcoming, key=lambda p: (p.watering.next_due, p.name.casefold()))
