"""Flask routes (contracts/routes.md)."""

from __future__ import annotations

from dataclasses import dataclass

from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from . import care, db, timeutil

bp = Blueprint("web", __name__)

ACTING_COOKIE = "acting_member"

# CSS badge class per watering state (style.css .badge-*)
WATER_BADGE = {
    care.NEVER: "never_watered",
    care.OK: "ok",
    care.DUE_TODAY: "due_today",
    care.OVERDUE: "overdue_water",
}
SUN_BADGE = {
    care.INSIDE: "ok",
    care.OUTSIDE: "outside",
    care.OVERDUE_INSIDE: "overdue_inside",
}
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


# --------------------------------------------------------------------------- helpers


def tz():
    return current_app.config["TIMEZONE"]


def now():
    return current_app.config["CLOCK"]()


def safe_next(default: str) -> str:
    """Only allow redirects to local paths."""
    target = request.values.get("next", "")
    if target.startswith("/") and not target.startswith("//"):
        return target
    return default


def acting_member():
    """The member chosen on this device (cookie), or None."""
    if "acting_member" not in g:
        member = None
        raw = request.cookies.get(ACTING_COOKIE, "")
        if raw.isdigit():
            member = db.get_member(int(raw))
        g.acting_member = member
    return g.acting_member


def resolve_member():
    """Member for a care event: explicit form field first, then this device's acting member."""
    raw = request.form.get("member_id", "")
    if raw.isdigit():
        return db.get_member(int(raw))
    return acting_member()


def set_acting_cookie(response, member_id: int):
    response.set_cookie(
        ACTING_COOKIE, str(member_id), max_age=COOKIE_MAX_AGE, samesite="Lax", httponly=True
    )
    return response


def register_template_helpers(app: Flask) -> None:
    @app.context_processor
    def inject():
        current_now = now()
        return {
            "acting_member": acting_member() if request else None,
            "all_members": db.list_members() if db.count_members() else [],
            "fmt_when": lambda dt: timeutil.format_when(dt, current_now, tz()),
            "fmt_time": lambda dt: timeutil.format_time(dt, tz()),
            "fmt_short": lambda dt: timeutil.format_short(dt, current_now, tz()),
            "fmt_date": lambda d: timeutil.format_date(d, timeutil.local_date(current_now, tz())),
            "local_input_value": lambda dt: timeutil.datetime_local_value(dt, tz()),
            "plural": timeutil.plural,
            "fmt_hours": lambda h: f"{h:g} hour" if h == 1 else f"{h:g} hours",
            "water_badge": WATER_BADGE.get,
            "sun_badge": SUN_BADGE.get,
            "has_plants_page": "web.plants" in current_app.view_functions,
        }


@bp.before_app_request
def require_household():
    """First use: nothing works until at least one member exists (FR-001)."""
    if request.endpoint in ("web.setup", "static"):
        return None
    if db.count_members() == 0:
        return redirect(url_for("web.setup"))
    return None


# --------------------------------------------------------------------------- members


@bp.route("/setup", methods=["GET", "POST"])
def setup():
    if db.count_members() > 0:
        return redirect(url_for("web.dashboard"))
    error = None
    names = [request.form.get("name1", ""), request.form.get("name2", "")]
    if request.method == "POST":
        try:
            cleaned = [db.clean_member_name(names[0])]
            if names[1].strip():
                second = db.clean_member_name(names[1])
                if second.casefold() == cleaned[0].casefold():
                    raise db.ValidationError("Please enter two different names.")
                cleaned.append(second)
            ids = [db.add_member(n) for n in cleaned]
        except db.ValidationError as exc:
            error = str(exc)
        else:
            flash(f"Welcome, {' and '.join(cleaned)}! Add your first plant to get started.")
            return set_acting_cookie(redirect(url_for("web.dashboard")), ids[0])
    return render_template("setup.html", error=error, names=names), 400 if error else 200


@bp.route("/members", methods=["GET", "POST"])
def members():
    error = None
    if request.method == "POST":
        try:
            name = db.clean_member_name(request.form.get("name"))
            db.add_member(name)
        except db.ValidationError as exc:
            error = str(exc)
        else:
            flash(f"Added {name}.")
            return redirect(url_for("web.members"))
    return render_template("members.html", error=error), 400 if error else 200


@bp.post("/members/<int:member_id>/rename")
def rename_member(member_id: int):
    if db.get_member(member_id) is None:
        return render_template("not_found.html"), 404
    try:
        db.rename_member(member_id, request.form.get("name"))
    except db.ValidationError as exc:
        return render_template("members.html", error=str(exc)), 400
    flash("Name updated.")
    return redirect(url_for("web.members"))


@bp.post("/members/<int:member_id>/delete")
def delete_member(member_id: int):
    if db.get_member(member_id) is None:
        return render_template("not_found.html"), 404
    if db.count_members() == 1:
        return render_template(
            "members.html", error="The household needs at least one person."
        ), 400
    try:
        db.delete_member(member_id)
    except db.ValidationError as exc:
        return render_template("members.html", error=str(exc)), 400
    flash("Removed.")
    return redirect(url_for("web.members"))


@bp.get("/choose-member")
def choose_member():
    return render_template("choose_member.html", next=safe_next(url_for("web.dashboard")))


@bp.post("/acting-member")
def set_acting_member():
    raw = request.form.get("member_id", "")
    member = db.get_member(int(raw)) if raw.isdigit() else None
    if member is None:
        return render_template("not_found.html"), 404
    flash(f"Recording as {member['name']} on this device.")
    return set_acting_cookie(redirect(safe_next(url_for("web.dashboard"))), member["id"])


# --------------------------------------------------------------------------- plant status


@dataclass
class PlantView:
    """A plant with its events and derived status, for templates."""

    plant: object
    events: list
    status: care.PlantStatus

    @property
    def id(self) -> int:
        return self.plant["id"]

    @property
    def watering(self) -> care.WateringStatus:
        return self.status.watering

    @property
    def sun(self) -> care.SunStatus:
        return self.status.sun


def build_views(plants) -> list[PlantView]:
    events = db.events_by_plant([p["id"] for p in plants])
    current, zone = now(), tz()
    views = []
    for p in plants:
        evs = events.get(p["id"], [])
        status = care.PlantStatus(
            id=p["id"],
            name=p["name"],
            location=p["location"],
            watering=care.watering_status(p["water_interval_days"], evs, current, zone),
            sun=care.sun_status(p["max_outside_hours"], evs, current),
        )
        views.append(PlantView(plant=p, events=evs, status=status))
    return views


def get_view_or_404(plant_id: int) -> PlantView:
    plant = db.get_plant(plant_id)
    if plant is None:
        abort(404)
    return build_views([plant])[0]


def render_plant(plant_id: int, error: str | None = None, status: int = 200):
    view = get_view_or_404(plant_id)
    return render_template("plant_detail.html", v=view, error=error), status


def parse_occurred_at():
    """Optional `occurred_at` (local datetime-local value); default now; never in the future."""
    raw = (request.form.get("occurred_at") or "").strip()
    current = now()
    if not raw:
        return current
    try:
        when = timeutil.parse_local_datetime(raw, tz())
    except ValueError as exc:
        raise db.ValidationError(str(exc)) from None
    if timeutil.is_future(when, current):
        raise db.ValidationError("That time is in the future. Care can only be recorded after it happens.")
    return when


def member_or_choose(default_next: str):
    """Return (member, None) or (None, redirect-to-choose-member)."""
    member = resolve_member()
    if member is None:
        return None, redirect(url_for("web.choose_member", next=safe_next(default_next)))
    return member, None


# --------------------------------------------------------------------------- dashboard


@bp.get("/")
def dashboard():
    """FR-023-FR-026: what needs attention, most urgent first, with one-tap actions."""
    views = build_views(db.list_plants())
    statuses = [v.status for v in views]
    groups = care.group_items(care.dashboard_items(statuses))
    return render_template(
        "dashboard.html",
        groups=groups,
        plant_count=len(views),
        upcoming=care.next_upcoming(statuses),
        inside_plants=[v for v in views if not v.sun.is_outside],
    )


# --------------------------------------------------------------------------- plants (US1)


@bp.get("/plants")
def plants():
    return render_template("plants.html", views=build_views(db.list_plants()))


@bp.route("/plants/new", methods=["GET"])
def new_plant():
    return render_template("plant_form.html", plant=None, form={})


@bp.post("/plants")
def create_plant():
    try:
        fields = db.clean_plant(request.form)
    except db.ValidationError as exc:
        return render_template("plant_form.html", plant=None, form=request.form, error=str(exc)), 400
    plant_id = db.create_plant(fields)
    flash(f"Added {fields['name']}.")
    return redirect(url_for("web.plant_detail", plant_id=plant_id))


@bp.get("/plants/<int:plant_id>")
def plant_detail(plant_id: int):
    return render_plant(plant_id)


@bp.route("/plants/<int:plant_id>/edit", methods=["GET", "POST"])
def edit_plant(plant_id: int):
    plant = db.get_plant(plant_id)
    if plant is None:
        abort(404)
    if request.method == "GET":
        return render_template("plant_form.html", plant=plant, form=plant)
    try:
        fields = db.clean_plant(request.form)
    except db.ValidationError as exc:
        return render_template("plant_form.html", plant=plant, form=request.form, error=str(exc)), 400
    db.update_plant(plant_id, fields)
    flash("Saved changes.")
    return redirect(url_for("web.plant_detail", plant_id=plant_id))


@bp.route("/plants/<int:plant_id>/delete", methods=["GET", "POST"])
def delete_plant(plant_id: int):
    plant = db.get_plant(plant_id)
    if plant is None:
        abort(404)
    if request.method == "GET":
        return render_template("confirm_delete.html", plant=plant)
    db.delete_plant(plant_id)
    flash(f"Removed {plant['name']}.")
    return redirect(url_for("web.plants"))


# --------------------------------------------------------------------------- care events


@bp.post("/plants/<int:plant_id>/water")
def water(plant_id: int):
    """FR-008: record a watering."""
    detail_url = url_for("web.plant_detail", plant_id=plant_id)
    with db.write_lock():
        view = get_view_or_404(plant_id)
        member, choose = member_or_choose(detail_url)
        if choose:
            return choose
        try:
            when = parse_occurred_at()
        except db.ValidationError as exc:
            return render_plant(plant_id, error=str(exc), status=400)
        db.add_event(plant_id, member["id"], care.WATERED, when)
    flash(f"{member['name']} watered {view.plant['name']}.")
    return redirect(safe_next(detail_url))


def record_sun_event(plant_id: int, kind: str, done_message: str):
    """FR-012/FR-015/FR-016: record moved outside or brought inside, enforcing the sequence."""
    detail_url = url_for("web.plant_detail", plant_id=plant_id)
    with db.write_lock():
        view = get_view_or_404(plant_id)
        member, choose = member_or_choose(detail_url)
        if choose:
            return choose
        try:
            when = parse_occurred_at()
        except db.ValidationError as exc:
            return render_plant(plant_id, error=str(exc), status=400)
        error = care.sun_event_error(kind, view.plant["max_outside_hours"], view.events, when, now())
        if error:
            return render_plant(plant_id, error=error, status=400)
        db.add_event(plant_id, member["id"], kind, when)
    flash(done_message.format(member=member["name"], plant=view.plant["name"]))
    return redirect(safe_next(detail_url))


@bp.post("/plants/<int:plant_id>/outside")
def move_outside(plant_id: int):
    return record_sun_event(plant_id, care.MOVED_OUTSIDE, "{member} moved {plant} outside.")


@bp.post("/plants/<int:plant_id>/inside")
def bring_inside(plant_id: int):
    return record_sun_event(plant_id, care.BROUGHT_INSIDE, "{member} brought {plant} inside.")


@bp.app_errorhandler(404)
def not_found(_exc):
    return render_template("not_found.html"), 404
