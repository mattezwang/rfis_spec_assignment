# Plant Care Tracker

A shared plant care tracker for two roommates. It replaces the handwritten chart on the fridge.
Each person records when they water a plant or move it outside, and the dashboard shows what
needs attention: plants overdue for water, plants never watered, plants due today, and plants
that are outside or overdue to come back in.

Built for 17-626 Requirements for Information Systems with spec-driven development using
GitHub Spec Kit. The work went from a manual spec, through the Spec Kit artifacts, to this
prototype.

## Run it

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run plant-tracker
```

Open <http://localhost:8000>. On first use the app asks for the household members' names.

To use it from a phone, keep it running on a computer at home and open
`http://<that computer's IP address>:8000` on the phone (same Wi-Fi). Both roommates see the
same data because it lives in one database file on that computer.

| Environment variable | Default | Purpose |
|----------------------|---------|---------|
| `PORT` | `8000` | Port to listen on |
| `HOST` | `0.0.0.0` | Interface to bind (use `127.0.0.1` for this computer only) |
| `PLANT_TRACKER_DB` | `./instance/plants.db` | SQLite database file |
| `PLANT_TRACKER_TZ` | system time zone | Household time zone, e.g. `America/New_York` |

## Tests

```bash
uv run pytest
```

There are 82 tests. Unit tests (`tests/unit/`) cover the status rules in
`src/plant_tracker/care.py` using fixed clocks. Integration tests (`tests/integration/`) drive
the web app, one file per user story. A browser walkthrough of the quickstart scenarios is
recorded in [docs/validation.md](docs/validation.md).

## How to use it

- **Dashboard** (home page): what needs attention, most urgent first. Tap **Water** or
  **Bring inside** to record it as the person shown in "Recording as". Open **Move a plant
  outside** to send a plant out for sun. The page refreshes every minute, so you see your
  roommate's updates.
- **Plants**: every plant with its status. Open a plant to record care as a specific person
  or at an earlier time (if you forgot to log it), see the full care history, delete a
  mistaken entry, edit the schedule, or remove the plant.
- **Household**: add or rename people. Pick your name in the "Recording as" bar on each of
  your devices.
- If you try to water a plant that isn't due yet, the app tells you who already watered it
  and when, and lets you water anyway or cancel.

## Project artifacts

The order below matches the work:

1. [docs/initial-spec.md](docs/initial-spec.md): the manually written specification (no AI)
2. [.specify/memory/constitution.md](.specify/memory/constitution.md): project principles (`/speckit-constitution`)
3. [specs/001-plant-care-tracker/spec.md](specs/001-plant-care-tracker/spec.md): refined spec with clarifications (`/speckit-specify`, `/speckit-clarify`)
4. [specs/001-plant-care-tracker/plan.md](specs/001-plant-care-tracker/plan.md), plus
   [research.md](specs/001-plant-care-tracker/research.md),
   [data-model.md](specs/001-plant-care-tracker/data-model.md),
   [contracts/routes.md](specs/001-plant-care-tracker/contracts/routes.md),
   [quickstart.md](specs/001-plant-care-tracker/quickstart.md) (`/speckit-plan`)
5. [specs/001-plant-care-tracker/tasks.md](specs/001-plant-care-tracker/tasks.md) (`/speckit-tasks`)
6. `src/`, `tests/`: the prototype (`/speckit-implement`)
7. [docs/speckit-log.md](docs/speckit-log.md): the input given to each Spec Kit command
8. [docs/traceability.md](docs/traceability.md): interview → goal → requirement → code → test
9. [docs/validation.md](docs/validation.md): browser validation results and screenshots

`git log` shows one commit per Spec Kit step and per implementation phase.

## Code layout

```text
src/plant_tracker/
  care.py       status rules: watering, sunlight, duplicate warning, dashboard order (pure functions)
  db.py         SQLite schema and queries (only plants, members, and care events are stored)
  web.py        Flask routes
  timeutil.py   local time handling and formatting
  templates/    server-rendered pages
  static/       stylesheet
tests/          unit and integration tests
```
