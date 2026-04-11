from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.routes.auth import _is_strong_password
from app.src.project.queries import get_projects_for_user, user_is_project_owner

from app.core import db
from app.tables import User, TimelineEvent, Project, Role


DashBP = Blueprint("dashboard", __name__)

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route("/")
def main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    display_name = (user.full_name or user.username) if user else "User"

    projects = get_projects_for_user(user_id)

    return render_template(
        "dashboard/home.html.j2",
        projects=projects,
        display_name=display_name,
    ), 200

@DashBP.route("/timeline")
def timeline():
    user_id = session["user_id"]

    projects = get_projects_for_user(user_id)

    events = (
        db.session.execute(
            select(TimelineEvent, Project.title)
            .join(Project, TimelineEvent.project_id == Project.id)
            .join(Role, Role.project_id == Project.id)
            .where(Role.user_id == user_id)
            .distinct()
            .order_by(Project.title, TimelineEvent.start_date, TimelineEvent.end_date)
        )
        .all()
    )

    timeline_events = []
    for event, project_title in events:
        timeline_events.append({
            'id': event.id,
            'project_id': event.project_id,
            'project_title': project_title,
            'content': event.title,
            'description': event.description,
            'start': event.start_date,
            'end': event.end_date,
            'missing_start': False
        })

    return render_template(
        "dashboard/timeline.html.j2",
        dashboard_title=f"Global Timeline",
        description="Visualize phases, events and deadlines across all your projects.",
        projects=projects,
        timeline_events=timeline_events,
    ), 200


@DashBP.route("/about-your-data")
def about_your_data():
    return render_template(
        "dashboard/about_your_data.html.j2",
    ), 200


@DashBP.route("/account-settings", methods=["GET", "POST"])
def account_settings():
    user = db.session.get(User, session["user_id"])
    if not user:
        return abort(404)

    if request.method == "POST":
        form_action = request.form.get("form_action", "change_password")

        if form_action == "clear_project_data":
            project_id = request.form.get("project_id", "")
            project = db.session.get(Project, project_id) if project_id else None

            if not project or not user_is_project_owner(user.id, project_id):
                flash("Select one of your projects to clear.", "error")
                return redirect(url_for("dashboard.account_settings"))

            from app.routes.project.settings import _delete_project_data

            project_title = project.title
            _delete_project_data(project_id)
            db.session.commit()
            flash(f'Cleared all data for "{project_title}".', "success")
            return redirect(url_for("dashboard.account_settings"))

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
            return redirect(url_for("dashboard.account_settings"))

        if not _is_strong_password(new_password):
            flash(
                "Password must be 10+ characters and include uppercase, lowercase, number, and special character.",
                "error",
            )
            return redirect(url_for("dashboard.account_settings"))

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("dashboard.account_settings"))

    owned_projects = (
        db.session.execute(
            select(Project)
            .join(Role, Role.project_id == Project.id)
            .where(
                Role.user_id == user.id,
                Role.role == "owner",
            )
            .order_by(Project.title.asc())
        )
        .scalars()
        .all()
    )

    return render_template(
        "dashboard/account_settings.html.j2",
        current_user=user,
        owned_projects=owned_projects,
    ), 200
