from flask import render_template, abort, request, jsonify
from sqlalchemy import select

from app.core import db
from app.tables import Project, TimelineEvent
from app.src.project.visualizations import *

from .project import ProjectBP

@ProjectBP.route("/<project_id>/visualizations/")
def visualizations(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)
    
    event_distribution_data = build_event_distribution(project_id)
    role_distribution_data = build_role_distribution(project_id)

    return render_template(
        "project/visualizations.html",
        project=project,
        active_project_id=project.id,
        project_tab="visualizations",
        event_distribution_data=event_distribution_data,
        role_distribution_data=role_distribution_data
    ), 200
