from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import insert, select

from app.src.database import db
from app.src.timeline_service import build_timeline_state
from app.src.util_functions import get_projects_for_user
from app.tables.files import File
from app.tables.people import Person
from app.tables.person_reports import PersonReport
from app.tables.project_people import ProjectPerson
from app.tables.projects import Project
from app.tables.users import User

DashBP = Blueprint("dashboard", __name__)


@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))


@DashBP.route("/")
def get_dashboard_main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    dashboard_title = f"Welcome, {username}"
    description = "Here are your projects."

    return render_template(
        "dashboard/dashboard_overview.html",
        dashboard_title=dashboard_title,
        description=description,
        projects=projects,
    ), 200


@DashBP.route("/<project_id>/")
def get_dashboard_project_home(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    people_rows = (
        db.session.execute(
            select(Person, ProjectPerson)
            .join(ProjectPerson, ProjectPerson.person_id == Person.id)
            .where(ProjectPerson.project_id == project_id)
            .order_by(Person.name.asc())
        )
        .all()
    )

    recent_files = (
        db.session.execute(
            select(File)
            .where(File.project_id == project_id)
            .order_by(File.upload_date.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )

    return render_template(
        "dashboard/dashboard_project_home.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        recent_files=recent_files,
    ), 200


@DashBP.route("/<project_id>/visualizations/")
def get_dashboard_project_visualizations(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    return render_template(
        "dashboard/dashboard_visualizations.html",
        project=project,
        active_project_id=project.id,
    ), 200


@DashBP.route("/<project_id>/timeline/", methods=["GET"])
def get_dashboard_project_timeline(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    timeline_state = build_timeline_state(project_id, request.args.get("file_id", ""))

    return render_template(
        "dashboard/dashboard_timeline.html",
        project=project,
        active_project_id=project.id,
        **timeline_state,
    ), 200


@DashBP.route("/<project_id>/people/")
def get_dashboard_project_people(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    project_member_ids = select(ProjectPerson.person_id).where(
        ProjectPerson.project_id == project_id
    )

    reporting_edges = (
        db.session.query(PersonReport.person_id, PersonReport.reports_to_id)
        .filter(PersonReport.person_id.in_(project_member_ids))
        .filter(PersonReport.reports_to_id.in_(project_member_ids))
        .all()
    )
    reporting_links = {f"{person_id}:{reports_to_id}" for person_id, reports_to_id in reporting_edges}

    people_rows = (
        db.session.execute(
            select(Person, ProjectPerson)
            .join(ProjectPerson, ProjectPerson.person_id == Person.id)
            .where(ProjectPerson.project_id == project_id)
            .order_by(Person.name.asc())
        )
        .all()
    )

    return render_template(
        "dashboard/dashboard_people.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        reporting_links=reporting_links,
    ), 200


@DashBP.route("/<project_id>/people/updatematrix", methods=["POST"])
def update_reporting_matrix(project_id):
    payload = request.get_json()

    person_id = payload["person_id"]
    manager_id = payload["manager_id"]
    checked = payload["checked"]

    is_checked = str(checked).lower() == "true" if isinstance(checked, str) else bool(checked)

    if is_checked:
        db.session.execute(
            insert(PersonReport).values(person_id=person_id, reports_to_id=manager_id)
        )
    else:
        db.session.query(PersonReport).filter(
            PersonReport.person_id == person_id,
            PersonReport.reports_to_id == manager_id,
        ).delete()

    db.session.commit()

    return jsonify(
        {
            "person_id": person_id,
            "manager_id": manager_id,
            "checked": is_checked,
        }
    ), 200
