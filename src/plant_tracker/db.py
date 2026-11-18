"""SQLite storage: schema, connection handling, and queries.

Only plants, members, and care events are stored. Status (overdue, outside, ...) is derived
in care.py and never written here (research.md R-3).
"""

from __future__ import annotations

import sqlite3

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS member (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(name)) BETWEEN 1 AND 40),
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plant (
    id                   INTEGER PRIMARY KEY,
    name                 TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 60),
    location             TEXT NOT NULL CHECK (length(trim(location)) BETWEEN 1 AND 60),
    water_interval_days  INTEGER NOT NULL CHECK (water_interval_days >= 1),
    max_outside_hours    REAL NOT NULL CHECK (max_outside_hours > 0 AND max_outside_hours <= 72),
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS care_event (
    id           INTEGER PRIMARY KEY,
    plant_id     INTEGER NOT NULL REFERENCES plant(id) ON DELETE CASCADE,
    member_id    INTEGER NOT NULL REFERENCES member(id) ON DELETE RESTRICT,
    kind         TEXT NOT NULL CHECK (kind IN ('watered', 'moved_outside', 'brought_inside')),
    occurred_at  TEXT NOT NULL,
    recorded_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_care_event_plant_kind_time
    ON care_event (plant_id, kind, occurred_at);
"""

MEMBER_NAME_MAX = 40
PLANT_TEXT_MAX = 60
MAX_OUTSIDE_HOURS = 72


class ValidationError(ValueError):
    """Raised when user input breaks a rule in data-model.md. The message is user-facing."""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_schema() -> None:
    get_db().executescript(SCHEMA)


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema()


def _now_iso() -> str:
    from .timeutil import to_iso

    return to_iso(current_app.config["CLOCK"]())


# --------------------------------------------------------------------------- members


def clean_member_name(raw: str | None) -> str:
    """data-model.md member.name: required, trimmed, 1-40 chars."""
    name = (raw or "").strip()
    if not name:
        raise ValidationError("Please enter a name.")
    if len(name) > MEMBER_NAME_MAX:
        raise ValidationError(f"Names can be at most {MEMBER_NAME_MAX} characters.")
    return name


def list_members() -> list[sqlite3.Row]:
    return get_db().execute(
        """
        SELECT m.id, m.name,
               (SELECT COUNT(*) FROM care_event e WHERE e.member_id = m.id) AS event_count
        FROM member m ORDER BY m.id
        """
    ).fetchall()


def get_member(member_id: int) -> sqlite3.Row | None:
    return get_db().execute("SELECT id, name FROM member WHERE id = ?", (member_id,)).fetchone()


def count_members() -> int:
    return get_db().execute("SELECT COUNT(*) FROM member").fetchone()[0]


def add_member(raw_name: str | None) -> int:
    name = clean_member_name(raw_name)
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO member (name, created_at) VALUES (?, ?)", (name, _now_iso())
        )
    except sqlite3.IntegrityError:
        raise ValidationError(f'"{name}" is already in the household.') from None
    conn.commit()
    return cur.lastrowid


def rename_member(member_id: int, raw_name: str | None) -> None:
    name = clean_member_name(raw_name)
    conn = get_db()
    try:
        conn.execute("UPDATE member SET name = ? WHERE id = ?", (name, member_id))
    except sqlite3.IntegrityError:
        raise ValidationError(f'"{name}" is already in the household.') from None
    conn.commit()


def delete_member(member_id: int) -> None:
    """Only members with no care events can be deleted (FR-001)."""
    conn = get_db()
    used = conn.execute(
        "SELECT COUNT(*) FROM care_event WHERE member_id = ?", (member_id,)
    ).fetchone()[0]
    if used:
        raise ValidationError(
            "This person has care history, so they can't be removed. You can rename them instead."
        )
    conn.execute("DELETE FROM member WHERE id = ?", (member_id,))
    conn.commit()


# --------------------------------------------------------------------------- plants


def _clean_text(raw: str | None, label: str) -> str:
    """data-model.md plant.name / plant.location: required, trimmed, 1-60 chars."""
    value = (raw or "").strip()
    if not value:
        raise ValidationError(f"Please enter a {label}.")
    if len(value) > PLANT_TEXT_MAX:
        raise ValidationError(f"The {label} can be at most {PLANT_TEXT_MAX} characters.")
    return value


def clean_plant(form) -> dict:
    """Validate plant fields per data-model.md; raise ValidationError with a friendly message."""
    name = _clean_text(form.get("name"), "plant name")
    location = _clean_text(form.get("location"), "location")

    raw_interval = (form.get("water_interval_days") or "").strip()
    if not raw_interval.isdigit() or int(raw_interval) < 1:
        raise ValidationError("Watering interval must be a whole number of days, at least 1.")
    interval = int(raw_interval)
    if interval > 365:
        raise ValidationError("Watering interval can be at most 365 days.")

    raw_hours = (form.get("max_outside_hours") or "").strip()
    try:
        hours = float(raw_hours)
    except ValueError:
        raise ValidationError("Time outside must be a number of hours, like 2 or 1.5.") from None
    if not (0 < hours <= MAX_OUTSIDE_HOURS):  # also rejects NaN
        raise ValidationError(
            f"Time outside must be more than 0 and at most {MAX_OUTSIDE_HOURS} hours."
        )

    return {
        "name": name,
        "location": location,
        "water_interval_days": interval,
        "max_outside_hours": hours,
    }


def create_plant(fields: dict) -> int:
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO plant (name, location, water_interval_days, max_outside_hours, created_at)
           VALUES (:name, :location, :water_interval_days, :max_outside_hours, :created_at)""",
        {**fields, "created_at": _now_iso()},
    )
    conn.commit()
    return cur.lastrowid


def update_plant(plant_id: int, fields: dict) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE plant SET name = :name, location = :location,
               water_interval_days = :water_interval_days, max_outside_hours = :max_outside_hours
           WHERE id = :id""",
        {**fields, "id": plant_id},
    )
    conn.commit()


def delete_plant(plant_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM plant WHERE id = ?", (plant_id,))
    conn.commit()


def get_plant(plant_id: int):
    return get_db().execute("SELECT * FROM plant WHERE id = ?", (plant_id,)).fetchone()


def list_plants():
    return get_db().execute("SELECT * FROM plant ORDER BY name COLLATE NOCASE, id").fetchall()


# --------------------------------------------------------------------------- care events


def add_event(plant_id: int, member_id: int, kind: str, occurred_at) -> int:
    """Insert a care event (data-model.md care_event.kind / occurred_at / member_id)."""
    from .timeutil import to_iso

    conn = get_db()
    cur = conn.execute(
        """INSERT INTO care_event (plant_id, member_id, kind, occurred_at, recorded_at)
           VALUES (?, ?, ?, ?, ?)""",
        (plant_id, member_id, kind, to_iso(occurred_at), _now_iso()),
    )
    conn.commit()
    return cur.lastrowid


def events_by_plant(plant_ids: list[int] | None = None) -> dict[int, list]:
    """All care events grouped by plant, newest first, as care.Event objects."""
    from .care import Event
    from .timeutil import from_iso

    sql = """SELECT e.id, e.plant_id, e.kind, e.occurred_at, e.member_id, m.name AS member_name
             FROM care_event e JOIN member m ON m.id = e.member_id"""
    params: tuple = ()
    if plant_ids is not None:
        if not plant_ids:
            return {}
        sql += f" WHERE e.plant_id IN ({','.join('?' * len(plant_ids))})"
        params = tuple(plant_ids)
    sql += " ORDER BY e.occurred_at DESC, e.id DESC"

    grouped: dict[int, list] = {}
    for row in get_db().execute(sql, params):
        grouped.setdefault(row["plant_id"], []).append(
            Event(
                kind=row["kind"],
                occurred_at=from_iso(row["occurred_at"]),
                member_name=row["member_name"],
                id=row["id"],
                member_id=row["member_id"],
            )
        )
    return grouped
