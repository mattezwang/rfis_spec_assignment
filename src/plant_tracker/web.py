"""Flask routes (contracts/routes.md)."""

from __future__ import annotations

from flask import (
    Blueprint,
    Flask,
    current_app,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from . import db, timeutil

bp = Blueprint("web", __name__)

ACTING_COOKIE = "acting_member"
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
            "fmt_date": lambda d: timeutil.format_date(d, timeutil.local_date(current_now, tz())),
            "local_input_value": lambda dt: timeutil.datetime_local_value(dt, tz()),
            "plural": timeutil.plural,
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


# --------------------------------------------------------------------------- dashboard


@bp.get("/")
def dashboard():
    return render_template("dashboard.html")


@bp.app_errorhandler(404)
def not_found(_exc):
    return render_template("not_found.html"), 404
