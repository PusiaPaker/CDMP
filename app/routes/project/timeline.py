from flask import render_template, abort, request

from app.core import db
from app.tables import Project

from .project import ProjectBP
from app.src.project.timeline import build_timeline_state

@ProjectBP.route("/<project_id>/visualizations/")
def visualizations(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    return render_template(
        "project/visualizations.html",
        project=project,
        active_project_id=project.id,
    ), 200

@ProjectBP.route("/<project_id>/timeline/", methods=["GET"])
def timeline(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    timeline_state = build_timeline_state(project_id, request.args.get("file_id", ""))

    return render_template(
        "project/timeline.html",
        project=project,
        active_project_id=project.id,
        **timeline_state,
    ), 200
