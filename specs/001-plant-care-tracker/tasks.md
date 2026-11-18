---

description: "Task list for the Shared Household Plant Care Tracker"
---

# Tasks: Shared Household Plant Care Tracker

**Input**: Design documents from `/specs/001-plant-care-tracker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routes.md, quickstart.md

**Tests**: Required. Constitution Principle V mandates unit tests for all status rules and at
least one integration test per user story. Within each story, write tests first and confirm they
fail before implementing.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested
on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

## Path Conventions

Single project: `src/plant_tracker/`, `tests/` at the repository root (see plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `pyproject.toml` (uv project, Python ≥3.11, Flask 3.x, pytest dev dependency, `plant-tracker` script entry, src layout) and `.gitignore` (`.venv/`, `__pycache__/`, `instance/`, `*.db`)
- [X] T002 Create package skeleton: `src/plant_tracker/__init__.py` with `create_app(config=None)` factory reading `PLANT_TRACKER_DB`, `PLANT_TRACKER_TZ`, and a `CLOCK` callable; `src/plant_tracker/__main__.py` serving on `0.0.0.0:$PORT` (default 8000)
- [X] T003 [P] Create `tests/conftest.py` with fixtures: `app` (temp DB file, frozen clock that tests can move), `client`, and helpers to create members/plants

**Checkpoint**: `uv sync` and `uv run pytest` succeed (no tests yet).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database, time handling, layout, and household members, which every story needs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement schema creation and connection handling in `src/plant_tracker/db.py`: tables `member`, `plant`, `care_event` with the constraints in data-model.md (`member.name` unique case-insensitive; `plant.water_interval_days`, `plant.max_outside_hours` CHECKs; `care_event.kind` CHECK; `care_event.plant_id` ON DELETE CASCADE; `care_event.member_id` ON DELETE RESTRICT), index `(plant_id, kind, occurred_at)`, `PRAGMA foreign_keys=ON`, per-request connection
- [X] T005 [P] Implement `src/plant_tracker/timeutil.py`: UTC now from app clock, `to_local()`, `local_today()`, `parse_local_datetime()` for `datetime-local` form values, ISO serialization, friendly formatting ("today 09:15", "yesterday", "Nov 10")
- [X] T006 [P] Unit tests for timeutil in `tests/unit/test_timeutil.py` (local date across midnight, parsing, future detection)
- [X] T007 Implement member queries in `src/plant_tracker/db.py`: list, add, rename, delete-if-unused, count events per member; validate `member.name` per data-model.md
- [X] T008 Create `src/plant_tracker/templates/base.html` (header with Dashboard / Plants / Members nav, "Recording as" switcher posting to `/acting-member`, flash messages, mobile viewport) and `src/plant_tracker/static/style.css` (mobile-first, no horizontal scroll at 360 px, group colors with text badges)
- [X] T009 Implement in `src/plant_tracker/web.py`: blueprint, redirect-to-`/setup` guard when no members exist, `GET/POST /setup`, `GET/POST /members`, `POST /members/<id>/rename`, `POST /members/<id>/delete`, `POST /acting-member` (cookie), safe local `next` redirect helper, and an `acting_member()` resolver (form `member_id` → cookie → none); templates `setup.html`, `members.html` (FR-001, FR-002)
- [X] T010 Integration tests in `tests/integration/test_members.py`: first use redirects to setup; setup creates members and sets cookie; duplicate or blank name rejected; member with events cannot be deleted; rename works

**Checkpoint**: The app starts, asks for names on first use, and shows an empty dashboard
placeholder.

---

## Phase 3: User Story 1 - Keep plants watered on their own schedules (Priority: P1) 🎯 MVP

**Goal**: Add, edit, and remove plants; record waterings with who and when; show last watered,
next due, due today, overdue, and never watered.

**Independent Test**: Add two plants with different intervals, record a watering for one, move
the clock, and confirm each status (spec US1 scenarios 1–6).

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Unit tests for `watering_status()` in `tests/unit/test_care.py`: never, ok with days until due, due today, overdue with day count, calendar-day boundary (watered 21:00 on a 1-day interval → due next day), interval edit recalculates, latest of several waterings wins, back-dated watering older than latest ignored for "last"
- [X] T012 [P] [US1] Integration tests in `tests/integration/test_us1_watering.py`: add plant → never watered; record watering → last watered by member + next due; advance clock → due today, overdue; edit interval → next due changes; back-dated watering; future time rejected; invalid plant fields rejected with 400; delete plant with confirmation

### Implementation for User Story 1

- [X] T013 [US1] Implement `WateringStatus` and `watering_status(plant, last_watering, today, tz)` in `src/plant_tracker/care.py` per data-model.md "WateringStatus"
- [X] T014 [US1] Implement plant and watering queries in `src/plant_tracker/db.py`: create / get / list / update / delete plant (validate `plant.name`, `plant.location`, `plant.water_interval_days`, `plant.max_outside_hours` per data-model.md); insert care event (`care_event.kind`, `care_event.occurred_at`, `care_event.member_id` per data-model.md); latest event of a kind per plant
- [X] T015 [US1] Implement routes in `src/plant_tracker/web.py`: `GET /plants`, `GET /plants/new`, `POST /plants`, `GET /plants/<id>`, `GET/POST /plants/<id>/edit`, `GET/POST /plants/<id>/delete`, `POST /plants/<id>/water` (member resolution, optional `occurred_at`, future rejected; duplicate warning comes in US4) per contracts/routes.md
- [X] T016 [P] [US1] Create templates `plant_form.html`, `plants.html`, `plant_detail.html` (watering status, last watered by whom, watering form with member select and optional time), `confirm_delete.html` in `src/plant_tracker/templates/`

**Checkpoint**: US1 works on its own; MVP can be demonstrated.

---

## Phase 4: User Story 2 - See what needs attention at a glance (Priority: P2)

**Goal**: Dashboard as the home screen listing plants that need attention, grouped and ordered by
urgency, with one-tap actions and an empty state.

**Independent Test**: With plants overdue, due today, never watered, and not due, open `/` and
verify order, distinct labels, one-tap watering, and the empty state (spec US2 scenarios 1, 3, 4).

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Unit tests for `dashboard_items()` in `tests/unit/test_care.py`: group order, within-group ordering (most overdue first, then name), ok plants excluded, empty-state next upcoming due
- [X] T018 [P] [US2] Integration tests in `tests/integration/test_us2_dashboard.py`: order in rendered HTML, text badges present, Water button on dashboard records with acting member and redirects back to `/`, no acting member → redirected to choose and nothing saved, empty state text, meta refresh present

### Implementation for User Story 2

- [X] T019 [US2] Implement `DashboardItem`, group constants, and `dashboard_items(plants_with_status)` plus `next_upcoming()` in `src/plant_tracker/care.py` per data-model.md "DashboardItem" (watering groups now; sun groups added in US3)
- [X] T020 [US2] Implement `GET /` in `src/plant_tracker/web.py`: load plants with latest events, compute statuses, build items
- [X] T021 [US2] Create `src/plant_tracker/templates/dashboard.html`: grouped sections with heading, color, badge, one action button per item posting with `next=/`, empty state, `<meta http-equiv="refresh" content="60">`

**Checkpoint**: US1 and US2 both work.

---

## Phase 5: User Story 3 - Don't forget plants that are outside (Priority: P3)

**Goal**: Record moved outside and brought inside with who and when; show bring-in-by time and
overdue-to-bring-inside; surface on the dashboard.

**Independent Test**: Set a short outside limit, move the plant outside, advance the clock past
the limit, confirm overdue, bring it inside, confirm the marks are cleared (spec US3 scenarios
1–4, US2 scenario 2).

### Tests for User Story 3 ⚠️

- [X] T022 [P] [US3] Unit tests for `sun_status()` and sun dashboard groups in `tests/unit/test_care.py`: inside with no events, outside with bring-in-by, overdue after limit, brought inside clears, limit edit recalculates, fractional hours, overdue-inside ranks above overdue-water, outside ranks last
- [X] T023 [P] [US3] Integration tests in `tests/integration/test_us3_sunlight.py`: move outside shows member and bring-in-by; second move outside rejected (400); bring inside when inside rejected; bring-inside time before move-outside rejected; overdue after clock moves; bring inside clears; dashboard groups and Bring inside button

### Implementation for User Story 3

- [X] T024 [US3] Implement `SunStatus` and `sun_status(plant, latest_sun_event, last_moved_outside, now)` in `src/plant_tracker/care.py` per data-model.md "SunStatus", and extend `dashboard_items()` with `overdue_inside` and `outside` groups
- [X] T025 [US3] Add sun queries in `src/plant_tracker/db.py` (latest sun event, last moved outside per plant) and routes `POST /plants/<id>/outside`, `POST /plants/<id>/inside` in `src/plant_tracker/web.py` enforcing the `care_event.kind` / `care_event.occurred_at` recording rules in data-model.md (FR-016)
- [X] T026 [US3] Update `plant_detail.html`, `plants.html`, `dashboard.html` with sun state, last moved outside by whom, bring-in-by, and Move outside / Bring inside actions

**Checkpoint**: US1–US3 work.

---

## Phase 6: User Story 4 - Coordinate care between roommates (Priority: P4)

**Goal**: Duplicate-watering warning with bypass, full care history, delete mistaken events,
shared state across devices.

**Independent Test**: Two test clients with different acting members: actions by one are visible
to the other; second watering triggers a warning naming the first member; Cancel saves nothing,
Water anyway saves; history lists events newest first; deleting an event recalculates (spec US4
scenarios 1–5).

### Tests for User Story 4 ⚠️

- [ ] T027 [P] [US4] Unit tests for `needs_duplicate_warning()` in `tests/unit/test_care.py`: warns when ok, not when due today / overdue / never, unaffected by sun state
- [ ] T028 [P] [US4] Integration tests in `tests/integration/test_us4_coordination.py`: two clients share state; warning page names last waterer; `confirm=1` records; cancel records nothing; warning still fires when the second client's page was stale; history newest first with member and action; delete event recalculates watering and sun status

### Implementation for User Story 4

- [ ] T029 [US4] Implement `needs_duplicate_warning(watering_status)` in `src/plant_tracker/care.py` and the warning flow in `POST /plants/<id>/water` in `src/plant_tracker/web.py` (re-read latest watering at submit time; return `confirm_water.html` with 200 unless `confirm=1`) (FR-020)
- [ ] T030 [P] [US4] Create `src/plant_tracker/templates/confirm_water.html` (plant, last waterer, relative time, next due; Water anyway / Cancel)
- [ ] T031 [US4] Add history query (all events for a plant, newest first, with member names) and event delete in `src/plant_tracker/db.py`; route `POST /events/<id>/delete` in `src/plant_tracker/web.py`; history table with delete buttons in `plant_detail.html` (FR-019, FR-021)

**Checkpoint**: All user stories work independently.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T032 [P] Write `README.md`: what it is, run steps, tests, environment variables, how to open from a phone, link to the spec artifacts
- [ ] T033 [P] Write `docs/traceability.md`: interview statement → goal → initial R# → FR → task → code location → test
- [ ] T034 Run the full test suite and fix failures
- [ ] T035 Run quickstart.md manual scenarios in a real browser (desktop and 360 px phone width), fix issues, and record results in `docs/validation.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none
- **Foundational (Phase 2)**: depends on Setup; blocks all stories
- **US1 (Phase 3)**: depends on Foundational
- **US2 (Phase 4)**: depends on Foundational; uses plants and watering from US1 to have data
  to show
- **US3 (Phase 5)**: depends on Foundational and US1 (plants); extends the US2 dashboard
- **US4 (Phase 6)**: depends on US1 (watering) and US3 (sun events in history)
- **Polish (Phase 7)**: after all stories

### Within Each User Story

- Tests first, confirmed failing
- `care.py` rules → `db.py` queries → `web.py` routes → templates
- Commit when the story's tests pass

### Parallel Opportunities

- T003 alongside T002; T005/T006 alongside T004
- In each story the unit-test and integration-test tasks are [P]
- Templates (T016, T030) can be written alongside routes once the route contract is fixed
- T032 and T033 in parallel

---

## Parallel Example: User Story 1

```bash
Task: "Unit tests for watering_status() in tests/unit/test_care.py"            # T011
Task: "Integration tests in tests/integration/test_us1_watering.py"           # T012
# then
Task: "Create templates plant_form/plants/plant_detail/confirm_delete.html"   # T016 alongside T015
```

---

## Implementation Strategy

### MVP First

1. Phase 1 Setup → Phase 2 Foundational
2. Phase 3 US1 → validate: plants and watering status work
3. Commit; this is a usable replacement for the fridge chart's core function

### Incremental Delivery

Each later phase (dashboard → sunlight → coordination) is committed separately once its tests
pass, then Polish validates everything against quickstart.md.

---

## Notes

- Every task traces to an FR via the story it belongs to; see `docs/traceability.md` (T033).
- Constrained fields cite data-model.md rather than restating limits.
- Commit after each phase.
