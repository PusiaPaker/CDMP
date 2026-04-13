from flask import render_template, session, request, redirect, url_for, jsonify, abort
from sqlalchemy import select, and_, insert
import re

from .project import ProjectBP
from app.src.people_accounts import get_user_by_email, reconcile_project_people_accounts
from app.src.project.queries import user_has_project_access, user_can_edit_project
from app.src.project.files import parse_csv_headers_preview, parse_xlsx_headers_preview, read_all_csv_rows, read_all_xlsx_rows

from app.tables import Project, ProjectPerson, PersonReport, Person
from app.core import db
from app.src.utilities import normalize_role_to_level

@ProjectBP.route("/<project_id>/people/", methods=['GET', 'POST'])
def people(project_id):
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if request.method == 'POST':
        if not user_can_edit_project(session["user_id"], project_id):
            return render_template("error/unauthorized.html"), 403

        name = request.form['name']
        role = request.form['role']
        title = request.form['title']
        email = request.form['email']
        phone = request.form['phone']

        # Got this Regex off google looks pretty legit
        phone_number_pattern = r"^(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}$"
        if not re.match(phone_number_pattern, phone):
            phone = ""

        existing_person = None
        if email:
            existing_person = db.session.execute(select(Person).where(Person.email == email)).first()

        if not existing_person:
            existing_user = get_user_by_email(email)
            if existing_user:
                new_person = Person(user_id=existing_user.id, name=name, email=email, phone=phone, title=title)
            else:
                new_person = Person(name=name, email=email, phone=phone, title=title)
            db.session.add(new_person)
            db.session.commit()

            db.session.add(ProjectPerson(project_id=project_id, person_id=new_person.id, role_level=role))
            db.session.commit()
        else:
            person = existing_person[0]
            existing_proj_person = db.session.execute(
                select(ProjectPerson).where(ProjectPerson.person_id == person.id)
            ).first()
            linked_existing_person = False
            existing_user = get_user_by_email(person.email)
            if existing_user and not person.user_id:
                person.user_id = existing_user.id
                linked_existing_person = True
            if not existing_proj_person:
                db.session.add(ProjectPerson(project_id=project_id, person_id=person.id, role_level=role))
            if not existing_proj_person or linked_existing_person:
                db.session.commit()

        return redirect(url_for('project.people', project_id=project_id))


    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if reconcile_project_people_accounts(project_id):
        db.session.commit()

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
        can_edit_project=user_can_edit_project(session["user_id"], project_id),
        ), 200

@ProjectBP.route("/<project_id>/people/<person_id>")
def delete_project_person(project_id, person_id):
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if not user_can_edit_project(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    projperson_to_delete = db.session.execute(
        select(ProjectPerson)
        .where(
            and_(ProjectPerson.project_id == project_id, ProjectPerson.person_id == person_id)
            )
        ).first()

    if projperson_to_delete:
        ## Deleting person from all projects deletes the person themselves from the database.
        if db.session.query(ProjectPerson).filter_by(person_id=person_id).count() == 1:
            person_to_delete = db.session.execute(
                select(Person)
                    .where(Person.id == person_id)
                ).first()
            db.session.delete(person_to_delete[0])

        db.session.delete(projperson_to_delete[0])
        db.session.commit()
    
    return redirect(url_for('project.people', project_id=project_id))


@ProjectBP.route("/<project_id>/people/updatematrix", methods=["POST"])
def update_reporting_matrix(project_id):
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if not user_can_edit_project(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

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
