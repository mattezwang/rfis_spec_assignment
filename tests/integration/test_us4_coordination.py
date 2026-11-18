"""US4: Coordinate care between roommates (FR-017-FR-022)."""

import re
from datetime import datetime

import pytest

from conftest import add_plant, member_id


def page(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def event_ids(html):
    return [int(x) for x in re.findall(r'action="/events/(\d+)/delete"', html)]


@pytest.fixture
def sam(app, household):
    """A second device (browser) where Sam is recording."""
    other = app.test_client()
    other.post("/acting-member", data={"member_id": str(member_id(app, "Sam"))})
    return other


def test_both_roommates_see_the_same_state(household, sam, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, "Monstera")
    household.post(f"/plants/{pid}/water", data={})

    html = page(sam, f"/plants/{pid}")
    assert "Monstera" in html
    assert "Last watered" in html and "Alex" in html
    assert "Recording as" in html
    assert re.search(r'<option value="\d+" selected>Sam</option>', html)


def test_duplicate_warning_names_who_watered(household, sam, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, "Monstera", interval=7)
    household.post(f"/plants/{pid}/water", data={})

    clock.set(datetime(2026, 11, 11, 18, 0))
    resp = sam.post(f"/plants/{pid}/water", data={"next": "/"})
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Already watered" in html
    assert "Alex" in html and "yesterday 09:00" in html
    assert "in 6 days" in html
    assert "Water anyway" in html and "Cancel" in html

    # Nothing was recorded by the warning.
    assert len(event_ids(page(household, f"/plants/{pid}"))) == 1


def test_water_anyway_records(household, sam, clock, app):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household)
    household.post(f"/plants/{pid}/water", data={})
    warning = sam.post(f"/plants/{pid}/water", data={"next": "/"}).get_data(as_text=True)
    assert 'name="confirm" value="1"' in warning
    sam_id = member_id(app, "Sam")
    assert f'name="member_id" value="{sam_id}"' in warning

    resp = sam.post(f"/plants/{pid}/water", data={"member_id": str(sam_id), "confirm": "1", "next": "/"})
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert len(event_ids(html)) == 2
    assert "Sam" in html.split("Last watered", 1)[1][:300]


def test_cancel_records_nothing(household, sam):
    pid = add_plant(household)
    household.post(f"/plants/{pid}/water", data={})
    warning = sam.post(f"/plants/{pid}/water", data={"next": "/"}).get_data(as_text=True)
    assert 'href="/">Cancel</a>' in warning
    assert len(event_ids(page(household, f"/plants/{pid}"))) == 1


def test_warning_uses_latest_saved_state_not_stale_page(household, sam, clock):
    """Both roommates had the dashboard open showing 'Never watered'; Alex taps first."""
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, "Fern")
    assert "Never watered" in page(household, "/") and "Never watered" in page(sam, "/")
    household.post(f"/plants/{pid}/water", data={"next": "/"})
    resp = sam.post(f"/plants/{pid}/water", data={"next": "/"})
    assert resp.status_code == 200
    assert "Already watered" in resp.get_data(as_text=True)


def test_history_newest_first_with_who_and_action(household, sam, clock):
    clock.set(datetime(2026, 11, 10, 8, 0))
    pid = add_plant(household, "Basil", hours=3)
    household.post(f"/plants/{pid}/water", data={})
    clock.set(datetime(2026, 11, 10, 10, 0))
    sam.post(f"/plants/{pid}/outside", data={})
    clock.set(datetime(2026, 11, 10, 12, 0))
    household.post(f"/plants/{pid}/inside", data={})

    html = page(sam, f"/plants/{pid}")
    history = html.split("Care history", 1)[1]
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>", history, re.S)
    assert [(a.strip(), w.strip(), t.strip()) for a, w, t in rows] == [
        ("Brought inside", "Alex", "today 12:00"),
        ("Moved outside", "Sam", "today 10:00"),
        ("Watered", "Alex", "today 08:00"),
    ]


def test_delete_mistaken_event_recalculates(household, clock):
    clock.set(datetime(2026, 11, 10, 9, 0))
    pid = add_plant(household, "Fern", hours=3)
    household.post(f"/plants/{pid}/water", data={})
    household.post(f"/plants/{pid}/outside", data={})
    html = page(household, f"/plants/{pid}")
    outside_id, water_id = event_ids(html)  # newest first (same time: later id first)

    resp = household.post(f"/events/{water_id}/delete", data={"next": f"/plants/{pid}"})
    assert resp.status_code == 302
    html = page(household, f"/plants/{pid}")
    assert "Never watered" in html

    household.post(f"/events/{outside_id}/delete", data={"next": f"/plants/{pid}"})
    html = page(household, f"/plants/{pid}")
    assert "Outside since" not in html and "Hasn't been outside yet" in html


def test_delete_unknown_event_404(household):
    assert household.post("/events/999/delete").status_code == 404
