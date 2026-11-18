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
