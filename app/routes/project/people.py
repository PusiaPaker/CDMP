import os
import uuid

from flask import render_template, session, request, redirect, url_for, jsonify
from sqlalchemy import select, exists, and_, insert

from .project import ProjectBP
from app.src.project.queries import user_has_project_access
from app.src.project.files import parse_csv_headers_preview, parse_xlsx_headers_preview, read_all_csv_rows, read_all_xlsx_rows

from app.tables import Project, ProjectPerson, PersonReport, Person
from app.core import db

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
    
    # role to level map (TEMPORARY)
    role_to_level = {
        'Director': 1,
        'Chief': 0,
        'Senior Manager': 2,
        'Senior': 3,
        'Manager': 4,
        'Frontline': 5
    }

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
            'level': role_to_level[pp.role_level]
        })

    print(people_nodes)

    return render_template(
        "project/people.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        reporting_links=reporting_links,
        people_nodes=people_nodes
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


@ProjectBP.route('/<project_id>/people/import', methods=['GET', 'POST'])
def people_import(project_id):
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/404.html"), 404

    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    if request.method == "GET":
        return render_template(
            "project/people_import_upload.html",
            active_project_id=project_id,
            project=project,
        ), 200

    f = request.files.get("uploaded_file")
    if not f or not f.filename:
        return render_template(
            "project/people_import_upload.html",
            active_project_id=project_id,
            project=project,
            error="Please choose a file.",
        ), 400

    ext = f.filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx"]:
        return render_template(
            "project/people_import_upload.html",
            active_project_id=project_id,
            project=project,
            error="Only .csv or .xlsx is supported.",
        ), 400

    instance_dir = os.path.join(os.getcwd(), "instance")
    imports_dir = os.path.join(instance_dir, "imports")
    os.makedirs(imports_dir, exist_ok=True)

    temp_id = str(uuid.uuid4())
    temp_name = f"{temp_id}.{ext}"
    temp_path = os.path.join(imports_dir, temp_name)

    f.save(temp_path)

    if ext == "csv":
        headers, preview = parse_csv_headers_preview(temp_path, preview_rows=10)
    else:
        headers, preview = parse_xlsx_headers_preview(temp_path, preview_rows=10)

    if not headers:
        return render_template(
            "project/people_import_upload.html",
            active_project_id=project_id,
            project=project,
            error="Could not read headers from file.",
        ), 400

    return render_template(
        "project/people_import_map.html",
        active_project_id=project_id,
        project=project,
        temp_path=temp_path,
        headers=headers,
        preview_rows=preview,
    ), 200


@ProjectBP.route('/<project_id>/people/import/commit', methods=['POST'])
def people_import_commit(project_id):
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/404.html"), 404

    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    temp_path = request.form.get("temp_path", "")
    if not temp_path or not os.path.exists(temp_path):
        return render_template("error/404.html"), 404

    ext = temp_path.split(".")[-1].lower()
    if ext == "csv":
        headers, rows = read_all_csv_rows(temp_path)
    else:
        headers, rows = read_all_xlsx_rows(temp_path)

    header_to_idx = {h: i for i, h in enumerate(headers)}

    def _idx_for(field_name: str):
        selected = request.form.get(field_name, "")
        if not selected or selected == "__none__":
            return None
        return header_to_idx.get(selected)

    name_i = _idx_for("map_name")
    email_i = _idx_for("map_email")
    phone_i = _idx_for("map_phone")
    title_i = _idx_for("map_title")
    role_level_i = _idx_for("map_role_level")

    def _get(row: list[str], idx: int | None):
        if idx is None:
            return None
        if idx >= len(row):
            return None
        v = row[idx]
        if v is None:
            return None
        s = str(v).strip()
        return s if s != "" else None

    created_people = 0
    assigned = 0
    skipped = 0

    for row in rows:
        name = _get(row, name_i)
        email = _get(row, email_i)
        phone = _get(row, phone_i)
        title = _get(row, title_i)
        role_level = _get(row, role_level_i)

        if email:
            email = email.strip().lower()

        if not name and not email:
            skipped += 1
            continue

        if not name:
            name = "Unknown"

        person = None

        if email:
            person = db.session.execute(
                select(Person).where(Person.email == email)
            ).scalar_one_or_none()

            if not person:
                person = Person(name=name, email=email, phone=phone, title=title)
                db.session.add(person)
                db.session.flush()
                created_people += 1
        else:
            person = Person(name=name, email=None, phone=phone, title=title)
            db.session.add(person)
            db.session.flush()
            created_people += 1

        already_assigned = db.session.execute(
            select(
                exists().where(
                    and_(
                        ProjectPerson.project_id == project_id,
                        ProjectPerson.person_id == person.id,
                    )
                )
            )
        ).scalar()

        if not already_assigned:
            db.session.add(ProjectPerson(project_id=project_id, person_id=person.id, role_level=role_level))
            assigned += 1


    db.session.commit()

    try:
        os.remove(temp_path)
    except OSError:
        pass

    return redirect(url_for("project.people", project_id=project_id))
