"""US3: Don't forget plants that are outside (FR-012-FR-016)."""

from datetime import datetime

from conftest import add_plant, member_id


def page(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def outside(client, pid, **data):
    return client.post(f"/plants/{pid}/outside", data={"next": f"/plants/{pid}", **data})


def inside(client, pid, **data):
    return client.post(f"/plants/{pid}/inside", data={"next": f"/plants/{pid}", **data})


def test_move_outside_shows_who_and_bring_in_time(household, clock, app):
    clock.set(datetime(2026, 11, 10, 10, 0))
    pid = add_plant(household, "Basil", "Kitchen", hours=3)
    resp = outside(household, pid, member_id=str(member_id(app, "Sam")))
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert "Outside since" in html and "today 10:00" in html and "Sam" in html
    assert "Bring in by" in html and "13:00" in html


def test_overdue_then_bring_inside_clears(household, clock):
    clock.set(datetime(2026, 11, 10, 10, 0))
    pid = add_plant(household, "Basil", hours=3)
    outside(household, pid)

    clock.set(datetime(2026, 11, 10, 13, 1))
    assert "Overdue to bring inside" in page(household, f"/plants/{pid}")

    resp = inside(household, pid)
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert "Overdue to bring inside" not in html
    assert "Outside since" not in html
    assert "Inside" in html
    assert "Last moved outside" in html  # history of who took it out stays visible


def test_cannot_move_outside_twice(household):
    pid = add_plant(household)
    outside(household, pid)
    resp = outside(household, pid)
    assert resp.status_code == 400
    assert "already outside" in resp.get_data(as_text=True)


def test_only_bring_inside_offered_when_outside(household):
    pid = add_plant(household)
    html = page(household, f"/plants/{pid}")
    assert f'action="/plants/{pid}/outside"' in html
    assert f'action="/plants/{pid}/inside"' not in html
    outside(household, pid)
    html = page(household, f"/plants/{pid}")
    assert f'action="/plants/{pid}/inside"' in html
    assert f'action="/plants/{pid}/outside"' not in html


def test_cannot_bring_inside_when_inside(household):
    pid = add_plant(household)
    resp = inside(household, pid)
    assert resp.status_code == 400
    assert "already inside" in resp.get_data(as_text=True)


def test_bring_inside_time_cannot_precede_move_outside(household, clock):
    clock.set(datetime(2026, 11, 10, 12, 0))
    pid = add_plant(household)
    outside(household, pid, occurred_at="2026-11-10T10:00")
    resp = inside(household, pid, occurred_at="2026-11-10T09:00")
    assert resp.status_code == 400
    assert "before it went outside" in resp.get_data(as_text=True)


def test_editing_limit_recalculates_bring_in_time(household, clock):
    clock.set(datetime(2026, 11, 10, 10, 0))
    pid = add_plant(household, "Basil", hours=3)
    outside(household, pid)
    household.post(
        f"/plants/{pid}/edit",
        data={"name": "Basil", "location": "Kitchen", "water_interval_days": "7", "max_outside_hours": "5"},
    )
    assert "15:00" in page(household, f"/plants/{pid}")


def test_dashboard_sun_groups_and_bring_inside_button(household, clock):
    clock.set(datetime(2026, 11, 10, 8, 0))
    late = add_plant(household, "Forgotten", hours=1)
    sunny = add_plant(household, "Sunny", hours=8)
    thirsty = add_plant(household, "Thirsty", interval=1)
    for pid in (late, sunny, thirsty):
        household.post(f"/plants/{pid}/water", data={"occurred_at": "2026-11-08T08:00"})
    household.post(f"/plants/{sunny}/water", data={})
    household.post(f"/plants/{late}/water", data={})
    outside(household, late)
    outside(household, sunny)

    clock.set(datetime(2026, 11, 10, 10, 0))
    household.get("/")  # consume flash messages
    html = page(household, "/")
    assert "Overdue to bring inside" in html and "Outside now" in html
    assert html.index("Forgotten") < html.index("Thirsty") < html.index("Sunny")
    assert f'action="/plants/{late}/inside"' in html

    resp = household.post(f"/plants/{late}/inside", data={"next": "/"})
    assert resp.headers["Location"] == "/"
    household.get("/")
    assert f'action="/plants/{late}/inside"' not in page(household, "/")


def test_move_outside_from_dashboard(household, clock):
    """FR-025: plant movement can be recorded from the dashboard."""
    clock.set(datetime(2026, 11, 10, 10, 0))
    pid = add_plant(household, "Basil", hours=3)
    html = page(household, "/")
    assert "Move a plant outside" in html
    assert f'action="/plants/{pid}/outside"' in html

    resp = household.post(f"/plants/{pid}/outside", data={"next": "/"})
    assert resp.headers["Location"] == "/"
    household.get("/")
    html = page(household, "/")
    assert "Outside now" in html
    assert f'action="/plants/{pid}/outside"' not in html
