from flask import Blueprint, render_template, abort, session, redirect, url_for, request

from app.tables import Project
from app.src.project.queries import (
    get_project_workspace_context,
    user_has_project_access,
)
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
        return render_template("error/404.html"), 404

    if not user_has_project_access(session["user_id"], project_id):
        return redirect(url_for('dashboard.get_dashboard_main'))

    workspace_context = get_project_workspace_context(project_id)

    return render_template(
        "project/home.html",
        project=project,
        active_project_id=project.id,
        project_tab="overview",
        **workspace_context,
    ), 200
