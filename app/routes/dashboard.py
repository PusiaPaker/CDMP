from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import select

from app.src.project.queries import get_projects_for_user

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
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    return render_template(
        "dashboard/home.html.j2",
        projects=projects,
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
        "dashboard/timeline.html",
        dashboard_title=f"Global Timeline",
        description="Visualize phases, events and deadlines across all your projects.",
        projects=projects,
        timeline_events=timeline_events,
    ), 200
