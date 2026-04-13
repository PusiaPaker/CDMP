from flask import Blueprint, render_template, abort, session, redirect, url_for, request
from sqlalchemy import select

from app.tables import Project, Person, ProjectPerson, File
from app.src.project.queries import user_has_project_access, user_can_edit_project, user_is_project_owner
from app.core import db


ProjectBP = Blueprint('project', __name__)

@ProjectBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("mainPage"))


@ProjectBP.route("/<project_id>/")
def home(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return render_template("error/404.html"), 404

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

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
            "project/home.html.j2",
            project=project,
            recent_files = recent_files,
            people_rows = people_rows,
            can_edit_project=user_can_edit_project(session["user_id"], project_id),
            is_owner=user_is_project_owner(session["user_id"], project_id),
        ), 200
