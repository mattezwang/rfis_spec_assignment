from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from plant_tracker import create_app

TZ = ZoneInfo("America/New_York")


class FrozenClock:
    """A clock tests can set and advance. Times are given in household local time."""

    def __init__(self, local: datetime):
        self.now = local.replace(tzinfo=TZ).astimezone(timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def set(self, local: datetime) -> None:
        self.now = local.replace(tzinfo=TZ).astimezone(timezone.utc)

    def advance(self, **kwargs) -> None:
        self.now = self.now + timedelta(**kwargs)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2026, 11, 10, 9, 0))


@pytest.fixture
def app(tmp_path, clock):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.db"),
            "TIMEZONE": TZ,
            "CLOCK": clock,
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def household(client):
    """Create members Alex and Sam via first-use setup; acting member is Alex."""
    resp = client.post("/setup", data={"name1": "Alex", "name2": "Sam"})
    assert resp.status_code == 302
    return client


def add_plant(client, name="Monstera", location="Living room", interval=7, hours=2):
    resp = client.post(
        "/plants",
        data={
            "name": name,
            "location": location,
            "water_interval_days": str(interval),
            "max_outside_hours": str(hours),
        },
    )
    assert resp.status_code == 302, resp.get_data(as_text=True)
    return int(resp.headers["Location"].rstrip("/").split("/")[-1])


def member_id(app, name):
    from plant_tracker import db

    with app.app_context():
        for m in db.list_members():
            if m["name"] == name:
                return m["id"]
    raise LookupError(name)
