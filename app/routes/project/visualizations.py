from flask import render_template, abort, request, jsonify
from sqlalchemy import select

from app.core import db
from app.tables import Project, TimelineEvent, Person, ProjectPerson, PersonReport
from app.src.project.visualizations import *
from app.src.utilities import normalize_role_to_level

from .project import ProjectBP

@ProjectBP.route("/<project_id>/visualizations/")
def visualizations(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)
    
    event_distribution_data = build_event_distribution(project_id)
    role_distribution_data = build_role_distribution(project_id)

    project_member_ids = select(ProjectPerson.person_id).where(
        ProjectPerson.project_id == project_id
    )

    reporting_edges = (
        db.session.query(PersonReport.person_id, PersonReport.reports_to_id)
        .filter(PersonReport.person_id.in_(project_member_ids))
        .filter(PersonReport.reports_to_id.in_(project_member_ids))
        .all()
    )

    reporting_links = {
        f"{person_id}:{reports_to_id}" for person_id, reports_to_id in reporting_edges
    }

    people_rows = (
        db.session.execute(
            select(Person, ProjectPerson)
            .join(ProjectPerson, ProjectPerson.person_id == Person.id)
            .where(ProjectPerson.project_id == project_id)
            .order_by(Person.name.asc())
        )
        .all()
    )

    people_nodes = []
    for p, pp in people_rows:
        reports_to = []
        for person_id, reports_to_id in reporting_edges:
            if person_id == p.id:
                reports_to.append(reports_to_id)

        people_nodes.append(
            {
                "id": p.id,
                "name": p.name,
                "title": p.title,
                "role": pp.role_level,
                "reports_to": reports_to,
                "level": normalize_role_to_level(pp.role_level),
            }
        )

    return render_template(
        "project/visualizations.html.j2",
        project=project,
        active_project_id=project.id,
        event_distribution_data=event_distribution_data,
        role_distribution_data=role_distribution_data,
        people_rows=people_rows,
        reporting_links=reporting_links,
        people_nodes=people_nodes,
    ), 200 
