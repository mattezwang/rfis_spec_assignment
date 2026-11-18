# Quickstart & Validation Guide

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)

## Run

```bash
uv sync
uv run plant-tracker            # serves on http://0.0.0.0:8000
```

Open `http://localhost:8000` on the host, or `http://<host-ip>:8000` from a phone on the same
network. Optional environment variables: `PLANT_TRACKER_DB` (database file path),
`PLANT_TRACKER_TZ` (IANA time zone such as `America/New_York`), `PORT`.

## Automated tests

```bash
uv run pytest
```

Expected: all unit tests (status rules in `care.py`) and integration tests (one file per user
story) pass.

## Manual validation scenarios

Use two browsers (or a phone and a laptop) to act as the two roommates.

1. **First use (FR-001)**: open the app with an empty database → you are asked for names.
   Enter "Alex" and "Sam" → dashboard says there are no plants yet.
2. **US1 Watering**: add "Monstera" / "Living room" / every 7 days / 2 hours outside → dashboard
   lists it under *Never watered*. Tap **Water** → it leaves the dashboard; the plant page shows
   "Last watered today by Alex", next due in 7 days.
3. **US1 Back-dating**: on another plant's page, record a watering with the time set to
   8 days ago → it shows *Overdue by 1 day* (with a 7-day interval).
4. **US2 Dashboard order**: with one plant overdue, one due today, one outside, and one past its
   bring-in time, confirm the group order: overdue inside → overdue water → due today → outside.
   Each group has a distinct color and text label.
5. **US3 Sunlight**: set "Basil" to 0.05 hours outside (3 minutes); tap **Move outside** → it
   shows "Bring in by <time>". Wait 3 minutes → it moves to *Overdue to bring inside*. Tap
   **Bring inside** → it leaves the dashboard.
6. **US4 Sharing**: as Sam in the second browser, the dashboard shows Alex's actions within one
   minute (auto-refresh) or on reload.
7. **US4 Duplicate warning**: as Sam, tap **Water** on Monstera (watered by Alex today) → the
   warning names Alex. **Cancel** records nothing; **Water anyway** records it.
8. **US4 History**: Monstera's page lists all events newest first; deleting the latest watering
   returns the plant to its previous status.

See [contracts/routes.md](contracts/routes.md) for routes and screen contents and
[data-model.md](data-model.md) for the status rules.
