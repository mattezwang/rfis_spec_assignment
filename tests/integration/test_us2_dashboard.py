"""US2: See what needs attention at a glance (FR-023-FR-026)."""

from datetime import datetime

from conftest import add_plant


def dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def water_at(client, pid, when):
    resp = client.post(f"/plants/{pid}/water", data={"occurred_at": when, "confirm": "1"})
    assert resp.status_code == 302


def test_attention_order_and_labels(household, clock):
    clock.set(datetime(2026, 11, 20, 9, 0))
    late = add_plant(household, "Fern", interval=7)
    due = add_plant(household, "Pothos", interval=7)
    fine = add_plant(household, "Cactus", interval=30)
    add_plant(household, "Basil", interval=2)  # never watered
    water_at(household, late, "2026-11-10T09:00")
    water_at(household, due, "2026-11-13T09:00")
    water_at(household, fine, "2026-11-19T09:00")

    dashboard(household)  # consume "X watered Y" flash messages
    html = dashboard(household)
    assert html.index("Fern") < html.index("Basil") < html.index("Pothos")
    assert "Cactus" not in html
    assert "Overdue by 3 days" in html
    assert "Never watered" in html
    assert "Due today" in html
    assert "Overdue for water" in html and "Due for water today" in html
    assert 'class="group group-overdue_water"' in html


def test_water_from_dashboard_is_one_tap(household, clock):
    clock.set(datetime(2026, 11, 20, 9, 0))
    pid = add_plant(household, "Basil", interval=2)
    assert "Basil" in dashboard(household)

    resp = household.post(f"/plants/{pid}/water", data={"next": "/"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"
    html = dashboard(household)
    assert "Alex watered Basil" in html  # confirmation message
    assert 'action="/plants/%d/water"' % pid not in html  # no longer needs attention


def test_dashboard_buttons_post_to_dashboard(household):
    pid = add_plant(household, "Basil")
    html = dashboard(household)
    assert f'action="/plants/{pid}/water"' in html
    assert '<input type="hidden" name="next" value="/">' in html


def test_empty_states(household, clock):
    html = dashboard(household)
    assert "No plants yet" in html

    clock.set(datetime(2026, 11, 20, 9, 0))
    pid = add_plant(household, "Cactus", interval=10)
    water_at(household, pid, "2026-11-20T08:00")
    html = dashboard(household)
    assert "All plants are taken care of" in html
    assert "Cactus" in html and "Mon Nov 30" in html  # next upcoming watering


def test_dashboard_auto_refreshes(household):
    assert '<meta http-equiv="refresh" content="60">' in dashboard(household)
