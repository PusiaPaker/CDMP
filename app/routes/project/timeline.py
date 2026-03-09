from flask import render_template, abort, request, jsonify
from sqlalchemy import select

from app.core import db
from app.tables import Project, TimelineEvent

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

    events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
        )
        .scalars().all()
    )

    timeline_events = []
    for event in events:
        timeline_events.append({
            'id': event.id,
            'content': event.title,
            'description': event.description,
            'start': event.start_date,
            'end': event.end_date,
            'missing_start': False,
        })

    return render_template(
        "project/timeline.html",
        project=project,
        active_project_id=project.id,
        timeline_events=timeline_events,
    ), 200

@ProjectBP.route("/<project_id>/timeline/debug", methods=["GET"])
def timeline_debug(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)
    
    events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
        )
        .scalars().all()
    )

    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date,
            'end_date': event.end_date
        })

    return jsonify(events_data)
