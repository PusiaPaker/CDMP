from flask import render_template, session, request, redirect, url_for, jsonify, abort
from sqlalchemy import select, exists, and_, insert

from .project import ProjectBP
from app.src.project.queries import user_has_project_access
from app.src.project.files import parse_csv_headers_preview, parse_xlsx_headers_preview, read_all_csv_rows, read_all_xlsx_rows

from app.tables import Project, ProjectPerson, PersonReport, Person
from app.core import db
from app.src.utilities import normalize_role_to_level

@ProjectBP.route("/<project_id>/people/")
def people(project_id):
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
    
    # nodes and edges for visjs stuff
    # need to pass as pure dictionary object (not python object) because it needs to be converted to json to use in javascript
    people_nodes = []
    for p, pp in people_rows:
        reports_to = []
        for person_id, reports_to_id in reporting_edges:
            if person_id == p.id:
                reports_to.append(reports_to_id)
        
        people_nodes.append({
            'id': p.id,
            'name': p.name,
            'title': p.title,
            'role': pp.role_level,
            'reports_to': reports_to,
            'level': normalize_role_to_level(pp.role_level)
        })

    return render_template(
        "project/people.html.j2",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        reporting_links=reporting_links,
        people_nodes=people_nodes,
        ), 200


@ProjectBP.route("/<project_id>/people/updatematrix", methods=["POST"])
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
