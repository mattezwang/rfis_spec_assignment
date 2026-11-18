"""US1: Keep plants watered on their own schedules (FR-003-FR-011)."""

from datetime import datetime

from conftest import add_plant, member_id


def page(client, url):
    resp = client.get(url)
    assert resp.status_code == 200, resp.status_code
    return resp.get_data(as_text=True)


def water(client, plant_id, **data):
    return client.post(f"/plants/{plant_id}/water", data={"next": f"/plants/{plant_id}", **data})


def test_add_plant_shows_never_watered(household):
    pid = add_plant(household, "Monstera", "Living room", interval=7)
    html = page(household, f"/plants/{pid}")
    assert "Monstera" in html and "Living room" in html
    assert "Never watered" in html
    assert "Every 7 days" in html
    assert "Monstera" in page(household, "/plants")


def test_record_watering_shows_who_and_next_due(household, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, interval=7)
    resp = water(household, pid)
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert "Last watered" in html
    assert "today 09:00" in html and "Alex" in html
    assert "Tue Nov 17" in html  # next due
    assert "Water in 7 days" in html


def test_due_today_then_overdue_until_watered(household, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, interval=7)
    water(household, pid)

    clock.set(datetime(2026, 11, 17, 8, 0))
    assert "Due today" in page(household, f"/plants/{pid}")

    clock.set(datetime(2026, 11, 18, 8, 0))
    assert "Overdue by 1 day" in page(household, f"/plants/{pid}")
    clock.set(datetime(2026, 11, 20, 8, 0))
    assert "Overdue by 3 days" in page(household, f"/plants/{pid}")

    water(household, pid)
    assert "Water in 7 days" in page(household, f"/plants/{pid}")


def test_edit_interval_recalculates(household, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, interval=7)
    water(household, pid)
    clock.set(datetime(2026, 11, 12, 9, 0))

    resp = household.post(
        f"/plants/{pid}/edit",
        data={
            "name": "Monstera deliciosa",
            "location": "Bedroom",
            "water_interval_days": "1",
            "max_outside_hours": "2",
        },
    )
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert "Monstera deliciosa" in html and "Bedroom" in html
    assert "Overdue by 1 day" in html


def test_backdated_watering(household, clock):
    clock.set(datetime(2026, 11, 10, 15, 0))
    pid = add_plant(household, interval=7)
    resp = water(household, pid, occurred_at="2026-11-10T08:30")
    assert resp.status_code == 302
    assert "today 08:30" in page(household, f"/plants/{pid}")

    resp = water(household, pid, occurred_at="2026-11-02T08:30", confirm="1")
    assert resp.status_code == 302
    assert "today 08:30" in page(household, f"/plants/{pid}")  # older entry doesn't replace


def test_future_watering_rejected(household, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household)
    resp = water(household, pid, occurred_at="2026-11-11T09:00")
    assert resp.status_code == 400
    assert "future" in resp.get_data(as_text=True)
    assert "Never watered" in page(household, f"/plants/{pid}")


def test_explicit_member_choice(household, app):
    pid = add_plant(household)
    water(household, pid, member_id=str(member_id(app, "Sam")))
    assert "Sam" in page(household, f"/plants/{pid}").split("Last watered", 1)[1][:300]


def test_no_member_redirects_to_choose_and_saves_nothing(household, app):
    pid = add_plant(household)
    household.delete_cookie("acting_member")
    resp = water(household, pid)
    assert resp.status_code == 302
    assert "/choose-member" in resp.headers["Location"]
    assert "Never watered" in page(household, f"/plants/{pid}")


def test_invalid_plant_rejected(household):
    bad = [
        {"name": "", "location": "Kitchen", "water_interval_days": "3", "max_outside_hours": "1"},
        {"name": "Fern", "location": "", "water_interval_days": "3", "max_outside_hours": "1"},
        {"name": "Fern", "location": "Kitchen", "water_interval_days": "0", "max_outside_hours": "1"},
        {"name": "Fern", "location": "Kitchen", "water_interval_days": "1.5", "max_outside_hours": "1"},
        {"name": "Fern", "location": "Kitchen", "water_interval_days": "3", "max_outside_hours": "0"},
        {"name": "Fern", "location": "Kitchen", "water_interval_days": "3", "max_outside_hours": "abc"},
    ]
    for data in bad:
        resp = household.post("/plants", data=data)
        assert resp.status_code == 400, data
    assert "Fern" not in page(household, "/plants")


def test_fractional_outside_hours_allowed(household):
    pid = add_plant(household, "Basil", "Kitchen", interval=2, hours=1.5)
    assert "1.5 hours" in page(household, f"/plants/{pid}")


def test_delete_plant_requires_confirmation(household):
    pid = add_plant(household, "Cactus", "Desk")
    html = page(household, f"/plants/{pid}/delete")
    assert "Remove Cactus" in html
    resp = household.post(f"/plants/{pid}/delete")
    assert resp.status_code == 302
    assert household.get(f"/plants/{pid}").status_code == 404
    assert "Cactus" not in page(household, "/plants")


def test_member_with_history_cannot_be_deleted(household, app):
    pid = add_plant(household)
    water(household, pid)
    resp = household.post(f"/members/{member_id(app, 'Alex')}/delete")
    assert resp.status_code == 400


def test_unknown_plant_404(household):
    assert household.get("/plants/999").status_code == 404
    assert household.post("/plants/999/water").status_code == 404
