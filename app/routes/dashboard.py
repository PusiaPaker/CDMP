from flask import Blueprint, render_template, session, redirect, request, url_for, abort
from flask_session import Session
from sqlalchemy import select

from app.tables.people import Person
from app.tables.project_people import ProjectPerson
from app.tables.users import User
from app.tables.files import File
from app.src.database import db
from app.tables.projects import Project
from app.src.util_functions import get_projects_for_user

DashBP= Blueprint('dashboard', __name__)

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route('/')
def get_dashboard_main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    dashboard_title = f'Welcome, {username}'
    description = "Here are your projects."

    return render_template(
        "dashboard/dashboard_overview.html",
        dashboard_title=dashboard_title,
        description=description,
        projects=projects,
    ), 200

@DashBP.route('/<project_id>/')
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

@DashBP.route('/<project_id>/visualizations/') 
def get_dashboard_project_visualizations(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    return render_template("dashboard/dashboard_visualizations.html", project=project, active_project_id=project.id), 200


@DashBP.route('/<project_id>/timeline/') 
def get_dashboard_project_timeline(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    return render_template("dashboard/dashboard_timeline.html", project=project, active_project_id=project.id), 200


@DashBP.route('/<project_id>/people/')
def get_dashboard_project_people(project_id):
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

    return render_template(
        "dashboard/dashboard_people.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        ), 200
