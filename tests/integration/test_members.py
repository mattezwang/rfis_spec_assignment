"""FR-001 / FR-002: household members without accounts."""

from conftest import member_id


def test_first_use_redirects_to_setup(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/setup")


def test_setup_creates_members_and_sets_acting_member(client, app):
    resp = client.post("/setup", data={"name1": "Alex", "name2": "Sam"})
    assert resp.status_code == 302
    assert "acting_member=" in resp.headers["Set-Cookie"]

    page = client.get("/").get_data(as_text=True)
    assert "Recording as" in page
    assert '<option value="%d" selected>Alex</option>' % member_id(app, "Alex") in page

    members = client.get("/members").get_data(as_text=True)
    assert "Alex" in members and "Sam" in members


def test_setup_only_once(household):
    resp = household.get("/setup")
    assert resp.status_code == 302


def test_setup_rejects_blank_and_duplicate_names(client):
    assert client.post("/setup", data={"name1": "  ", "name2": ""}).status_code == 400
    resp = client.post("/setup", data={"name1": "Alex", "name2": "alex"})
    assert resp.status_code == 400
    assert "two different names" in resp.get_data(as_text=True)
    # Nothing was created, so we are still on first use.
    assert client.get("/").status_code == 302


def test_add_and_rename_member(household, app):
    resp = household.post("/members", data={"name": "Jordan"})
    assert resp.status_code == 302
    jid = member_id(app, "Jordan")

    assert household.post("/members", data={"name": "jordan"}).status_code == 400

    resp = household.post(f"/members/{jid}/rename", data={"name": "Jo"})
    assert resp.status_code == 302
    assert "Jo" in household.get("/members").get_data(as_text=True)


def test_member_without_events_can_be_deleted(household, app):
    household.post("/members", data={"name": "Jordan"})
    jid = member_id(app, "Jordan")
    resp = household.post(f"/members/{jid}/delete")
    assert resp.status_code == 302
    try:
        member_id(app, "Jordan")
        raise AssertionError("Jordan should have been deleted")
    except LookupError:
        pass


def test_switch_acting_member(household, app):
    sam = member_id(app, "Sam")
    resp = household.post("/acting-member", data={"member_id": str(sam), "next": "/members"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/members")
    page = household.get("/members").get_data(as_text=True)
    assert f'<option value="{sam}" selected>Sam</option>' in page


def test_acting_member_rejects_external_redirect(household, app):
    sam = member_id(app, "Sam")
    resp = household.post(
        "/acting-member", data={"member_id": str(sam), "next": "//evil.example"}
    )
    assert resp.headers["Location"] == "/"
