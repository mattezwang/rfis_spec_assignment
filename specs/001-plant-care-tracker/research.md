# Research & Decisions: Shared Household Plant Care Tracker

No `NEEDS CLARIFICATION` items remained in Technical Context. These are the technology and
design decisions the plan relies on.

## R-1 Web framework

- **Decision**: Flask 3.x with Jinja2 server-rendered templates.
- **Rationale**: Smallest mainstream option that gives routing, templates, and a test client.
  Server rendering means no front-end build and works on any phone browser (Constitution IV).
- **Alternatives considered**: FastAPI + a JS front end (two halves to build and keep in sync;
  async not needed); Django (admin/ORM/auth far beyond scope); a desktop or CLI app (fails
  FR-017: both roommates need it on their own devices).

## R-2 Persistence

- **Decision**: Standard-library `sqlite3`, one database file, schema created with
  `CREATE TABLE IF NOT EXISTS` on startup, `PRAGMA foreign_keys = ON`.
- **Rationale**: One file is the shared source of truth (Constitution III); no server to run;
  transactions make concurrent submissions from two phones safe at this scale.
- **Alternatives considered**: SQLAlchemy (extra layer for three tables); JSON file (no
  transactions, risk of lost writes when both roommates submit at once).

## R-3 Derived, not stored, status

- **Decision**: Store only plants and care events. Compute last watered, next due, overdue,
  outside / bring-in-by, and dashboard order on every request in `care.py`.
- **Rationale**: Deleting a mistaken event (FR-021) or editing a schedule (FR-006) then
  "recalculates" for free; nothing can be marked done without an event (FR-022).
- **Alternatives considered**: Status columns updated on write (can drift; needs recalculation
  code paths for edits and deletions).

## R-4 Time handling

- **Decision**: Store `occurred_at` as UTC ISO-8601 text. Convert to local time for display and
  for calendar-day rules. Local zone comes from `PLANT_TRACKER_TZ` (IANA name) if set, otherwise
  the server's system zone. Rule functions receive `now` and `today` as parameters; the app gets
  them from a configurable clock so tests can freeze time.
- **Rationale**: Clarification 2 requires calendar-day due logic in local time. Injecting the
  clock makes "it is now Nov 18" testable (Constitution V).
- **Alternatives considered**: Store local times (breaks across DST changes); `freezegun`
  (an extra dependency for what a parameter does).

## R-5 Acting member without accounts

- **Decision**: The header shows "Recording as: Alex · switch". Choosing a member sets a cookie
  on that device. Dashboard action buttons use it, so watering is one tap (SC-001). On the plant
  page the member and time can be chosen explicitly. If no member is selected, an action sends
  the user to choose one first and does not record anything.
- **Rationale**: Meets FR-001 (a member is always chosen) and FR-002 (no passwords) without
  JavaScript. The cookie stores only a member id, not care data (Constitution III).
- **Alternatives considered**: A member dropdown on every button (more taps and clutter on the
  dashboard); login (out of scope).

## R-6 Duplicate-watering warning flow

- **Decision**: `POST /plants/<id>/water` re-reads the plant's latest watering inside the
  request. If the plant is not yet due and the form lacks `confirm=1`, nothing is saved and a
  warning page is returned naming who watered it and when, with "Water anyway" (re-POST with
  `confirm=1`) and "Cancel".
- **Rationale**: Checking on the server at submit time covers the case where both roommates
  press Water at almost the same time (spec edge case).
- **Alternatives considered**: A JS `confirm()` from page data (stale if the other roommate
  just watered).

## R-7 Live sharing

- **Decision**: `<meta http-equiv="refresh" content="60">` on the dashboard only.
- **Rationale**: Meets FR-017 / SC-005 (visible within one minute) with zero JS; forms on other
  pages are not interrupted by refreshes.
- **Alternatives considered**: WebSockets or server-sent events (unjustified complexity for two
  users).

## R-8 Dashboard grouping

- **Decision**: One dashboard entry per attention reason, so a plant that is both overdue for
  water and outside appears in both groups, each with its own action. Groups in order:
  overdue to bring inside (earliest bring-in-by first) → overdue for water (most days overdue
  first) → never watered → due today → outside (earliest bring-in-by first). Each group has a
  heading, color, and text badge.
- **Rationale**: FR-023/FR-024 ordering. Separate entries keep each action unambiguous.
- **Alternatives considered**: One row per plant with combined badges (harder to order by
  urgency and to give one obvious action).

## R-9 Testing approach

- **Decision**: pytest; unit tests for every rule in `care.py`; integration tests per user story
  through `app.test_client()` with a temporary DB and a frozen clock; a manual browser walkthrough
  of `quickstart.md` before release.
- **Rationale**: Constitution V; the test client exercises routing, templates, DB, and rules
  together without a browser.
