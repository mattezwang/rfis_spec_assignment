# Implementation Plan: Shared Household Plant Care Tracker

**Branch**: `001-plant-care-tracker` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-plant-care-tracker/spec.md`

## Summary

A small web app that two roommates open from their own phones or laptops on the home network.
They add plants with a watering interval (days) and an outside limit (hours), record waterings
and sun movements under their own name, and land on a dashboard that lists what needs attention
ordered by urgency. All state lives in one SQLite file on the machine running the app, so both
roommates see the same data (FR-017). Plant status is never stored; it is derived from the
plant's schedule and its care events by pure functions that take the current time as input,
which makes the overdue / due-today / bring-inside rules directly unit-testable (Constitution V).
Pages are rendered on the server with Flask + Jinja; the only client-side behavior is a
dashboard meta-refresh every 60 seconds (FR-017, SC-005).

## Technical Context

**Language/Version**: Python 3.11+ (developed on 3.13)

**Primary Dependencies**: Flask 3.x (routing, Jinja2 templates). Standard library `sqlite3`,
`zoneinfo`, `datetime`. No ORM, no front-end framework, no JavaScript build.

**Storage**: One SQLite file (`instance/plants.db` by default; path configurable). Schema created
on startup. Foreign keys on.

**Testing**: pytest. Unit tests for `care.py` (status rules) with fixed clocks; integration tests
per user story through Flask's test client against a temporary database; a manual browser
walkthrough from `quickstart.md`.

**Target Platform**: Any machine with Python 3.11+ on the household network (macOS, Linux,
Windows); clients are mobile and desktop browsers.

**Project Type**: Server-rendered web application (single project).

**Performance Goals**: Pages render in well under 1 s for 20 plants and a few thousand care
events (SC-003). No tuning needed at this scale.

**Constraints**: No authentication (FR-002). Readable on a 360 px-wide phone screen without
horizontal scrolling (SC-007). Dashboard reachable and actionable in at most two taps (SC-001).
Status must not depend on color alone (FR-024).

**Scale/Scope**: 1 household, 2+ members, up to ~20 plants, ~8 screens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|-----------|-------|--------|
| I. Stakeholder-driven scope | Every route and screen maps to an FR (see [contracts/routes.md](contracts/routes.md)); notifications, auto-calculation, photos, fertilizing, accounts are absent. | PASS |
| II. People record care | State is derived only from `care_event` rows created by explicit POSTs with a member; no scheduler, no background jobs; overdue persists until an event exists. | PASS |
| III. One shared source of truth | Single SQLite file on the server; the only browser-side state is a cookie remembering which member is acting on that device (a convenience, not care data). | PASS |
| IV. Simplicity first | One process, Flask + stdlib, server-rendered HTML, no JS build, no auth. | PASS |
| V. Tested care logic | All status rules in `care.py` as pure functions taking `now`; unit-tested. Each user story has an integration test. | PASS |

Post-design re-check (after Phase 1): still PASS. The design adds no layers beyond `care.py`
(rules), `db.py` (queries), and `web.py` (routes).

## Project Structure

### Documentation (this feature)

```text
specs/001-plant-care-tracker/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Entities, schema, derived state, validation
├── quickstart.md        # Run and validation guide
├── contracts/
│   └── routes.md        # HTTP routes / screens contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Created by /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml                 # uv project, Flask + pytest, `plant-tracker` entry point
src/plant_tracker/
├── __init__.py                # create_app(config) factory
├── __main__.py                # `python -m plant_tracker` / `plant-tracker` runner
├── care.py                    # Pure status rules (watering, sun, duplicate warning, dashboard)
├── db.py                      # SQLite connection, schema, query + write helpers
├── web.py                     # Flask routes (blueprint)
├── timeutil.py                # Local-time conversion and form parsing
├── templates/
│   ├── base.html              # Layout, nav, acting-member switcher
│   ├── setup.html             # First-use member entry
│   ├── dashboard.html
│   ├── plants.html            # All plants with status
│   ├── plant_form.html        # Add / edit
│   ├── plant_detail.html      # Status, actions with time + member, history
│   ├── confirm_water.html     # Duplicate-watering warning
│   ├── confirm_delete.html
│   └── members.html
└── static/
    └── style.css

tests/
├── conftest.py                # app + client fixtures, temp DB, fixed clock
├── unit/
│   └── test_care.py
└── integration/
    ├── test_us1_watering.py
    ├── test_us2_dashboard.py
    ├── test_us3_sunlight.py
    └── test_us4_coordination.py
```

**Structure Decision**: Single project with a `src/` layout. Separating `care.py` (pure rules)
from `db.py` and `web.py` is the one structural split, and it exists to satisfy Constitution V.

## Complexity Tracking

No constitution violations to justify.
