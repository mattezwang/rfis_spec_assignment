"""Unit tests for the status rules in care.py (Constitution Principle V)."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from plant_tracker import care
from plant_tracker.care import Event

NY = ZoneInfo("America/New_York")


def at(y, mo, d, h=9, mi=0):
    """A household-local time as aware UTC."""
    return datetime(y, mo, d, h, mi, tzinfo=NY).astimezone(timezone.utc)


def watered(when, who="Alex", id=None):
    return Event(kind=care.WATERED, occurred_at=when, member_name=who, id=id)


# --------------------------------------------------------------------------- US1 watering


class TestWateringStatus:
    def test_never_watered(self):
        s = care.watering_status(7, [], at(2026, 11, 10), NY)
        assert s.state == care.NEVER
        assert s.last is None and s.next_due is None

    def test_ok_with_days_until_due(self):
        s = care.watering_status(7, [watered(at(2026, 11, 10))], at(2026, 11, 12), NY)
        assert s.state == care.OK
        assert s.next_due == date(2026, 11, 17)
        assert s.days_until_due == 5
        assert s.last.member_name == "Alex"

    def test_due_today(self):
        s = care.watering_status(7, [watered(at(2026, 11, 10))], at(2026, 11, 17, 6), NY)
        assert s.state == care.DUE_TODAY

    def test_overdue_counts_days_and_persists(self):
        events = [watered(at(2026, 11, 10))]
        s = care.watering_status(7, events, at(2026, 11, 18), NY)
        assert s.state == care.OVERDUE and s.days_overdue == 1
        s = care.watering_status(7, events, at(2026, 11, 25), NY)
        assert s.state == care.OVERDUE and s.days_overdue == 8

    def test_calendar_day_boundary(self):
        # Watered 21:00 on a 1-day schedule: due the next calendar day, not 24 hours later.
        events = [watered(at(2026, 11, 10, 21))]
        assert care.watering_status(1, events, at(2026, 11, 11, 8), NY).state == care.DUE_TODAY
        assert care.watering_status(1, events, at(2026, 11, 12, 0, 30), NY).state == care.OVERDUE

    def test_interval_edit_recalculates(self):
        events = [watered(at(2026, 11, 10))]
        now = at(2026, 11, 14)
        assert care.watering_status(7, events, now, NY).state == care.OK
        s = care.watering_status(3, events, now, NY)
        assert s.state == care.OVERDUE and s.next_due == date(2026, 11, 13)

    def test_latest_watering_wins(self):
        events = [watered(at(2026, 11, 1), "Sam"), watered(at(2026, 11, 9), "Alex")]
        s = care.watering_status(7, events, at(2026, 11, 10), NY)
        assert s.last.member_name == "Alex"
        assert s.next_due == date(2026, 11, 16)

    def test_backdated_older_entry_does_not_replace_latest(self):
        # Recorded later, but happened earlier.
        events = [watered(at(2026, 11, 9), "Alex", id=1), watered(at(2026, 11, 2), "Sam", id=2)]
        s = care.watering_status(7, events, at(2026, 11, 10), NY)
        assert s.last.member_name == "Alex"

    def test_other_event_kinds_ignored(self):
        events = [Event(kind=care.MOVED_OUTSIDE, occurred_at=at(2026, 11, 9), member_name="Sam")]
        assert care.watering_status(7, events, at(2026, 11, 10), NY).state == care.NEVER

    def test_label(self):
        today = at(2026, 11, 10)
        assert care.watering_status(7, [], today, NY).label == "Never watered"
        assert care.watering_status(7, [watered(at(2026, 11, 3))], today, NY).label == "Due today"
        assert (
            care.watering_status(7, [watered(at(2026, 11, 1))], today, NY).label
            == "Overdue by 2 days"
        )
        assert (
            care.watering_status(7, [watered(at(2026, 11, 9))], today, NY).label
            == "Water in 6 days"
        )


# --------------------------------------------------------------------------- US2 dashboard


def status(id, name, interval, events, now, sun=None):
    return care.PlantStatus(
        id=id,
        name=name,
        location="Somewhere",
        watering=care.watering_status(interval, events, now, NY),
        sun=sun,
    )


class TestDashboard:
    def setup_method(self):
        self.now = at(2026, 11, 20)

    def test_groups_in_urgency_order_and_ok_excluded(self):
        n = self.now
        plants = [
            status(1, "Due", 7, [watered(at(2026, 11, 13))], n),
            status(2, "Fine", 7, [watered(at(2026, 11, 19))], n),
            status(3, "New", 7, [], n),
            status(4, "Late", 7, [watered(at(2026, 11, 10))], n),
        ]
        items = care.dashboard_items(plants)
        assert [(i.group, i.plant.name) for i in items] == [
            (care.G_OVERDUE_WATER, "Late"),
            (care.G_NEVER_WATERED, "New"),
            (care.G_DUE_TODAY, "Due"),
        ]

    def test_most_overdue_first_then_name(self):
        n = self.now
        plants = [
            status(1, "b-one-day", 7, [watered(at(2026, 11, 12))], n),
            status(2, "z-five-days", 7, [watered(at(2026, 11, 8))], n),
            status(3, "a-one-day", 7, [watered(at(2026, 11, 12))], n),
        ]
        names = [i.plant.name for i in care.dashboard_items(plants)]
        assert names == ["z-five-days", "a-one-day", "b-one-day"]

    def test_grouping_helper_keeps_order_and_skips_empty(self):
        n = self.now
        plants = [status(1, "New", 7, [], n), status(2, "Due", 7, [watered(at(2026, 11, 13))], n)]
        groups = care.group_items(care.dashboard_items(plants))
        assert [g.key for g in groups] == [care.G_NEVER_WATERED, care.G_DUE_TODAY]
        assert groups[0].title == "Never watered"

    def test_next_upcoming(self):
        n = self.now
        plants = [
            status(1, "Later", 7, [watered(at(2026, 11, 19))], n),
            status(2, "Sooner", 3, [watered(at(2026, 11, 19))], n),
        ]
        assert care.dashboard_items(plants) == []
        assert care.next_upcoming(plants).name == "Sooner"
        assert care.next_upcoming([]) is None
