from flask import Blueprint, render_template, abort, session, redirect, url_for, request
from sqlalchemy import select

from app.tables import Project, Person, ProjectPerson, File
from app.core import db


ProjectBP = Blueprint('project', __name__)

@ProjectBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))


@ProjectBP.route("/<project_id>/")
def home(project_id):
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
        "project/home.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        recent_files=recent_files,
    ), 200
