"""Shared Household Plant Care Tracker."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(config: dict | None = None) -> Flask:
    """Build the Flask app.

    Config keys:
      DATABASE  path to the SQLite file (env PLANT_TRACKER_DB, default instance/plants.db)
      TIMEZONE  a tzinfo for the household's local time (env PLANT_TRACKER_TZ, default system)
      CLOCK     zero-arg callable returning an aware UTC datetime (tests freeze it)
    """
    app = Flask(__name__)

    tz_name = os.environ.get("PLANT_TRACKER_TZ")
    default_db = Path.cwd() / "instance" / "plants.db"
    app.config.update(
        SECRET_KEY=os.environ.get("PLANT_TRACKER_SECRET", "plant-tracker-household"),
        DATABASE=os.environ.get("PLANT_TRACKER_DB", str(default_db)),
        TIMEZONE=ZoneInfo(tz_name) if tz_name else None,
        CLOCK=_utc_now,
    )
    if config:
        app.config.update(config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    from . import db, web

    db.init_app(app)
    app.register_blueprint(web.bp)
    web.register_template_helpers(app)
    return app
