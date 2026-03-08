from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify, abort
from sqlalchemy import select, exists, and_, insert
import pandas as pd
import os
import uuid

from app.core import db
from app.tables import Project, ProjectPerson, Person

from app.src.project.files import path_to_file_from_disk
from .project import ProjectBP
from app.src.project.queries import user_has_project_access
from app.src.project.files import parse_csv_headers_preview, parse_xlsx_headers_preview, read_all_csv_rows, read_all_xlsx_rows

DataBP = Blueprint('data', __name__)

# The plan here is that this endpoint will take care of
# importing a spreadsheet and mapping what columns go to where.
# this is upposed to be flexible enough to work with any kind of spreadsheet (people, timeline, ...)
@DataBP.route('/<project_id>/<table_type>/columnmapper', methods=['POST', 'GET'])
def column_mapper(project_id, table_type):
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
        headers, preview = parse_csv_headers_preview(temp_path, preview_rows=6)
    else:
        headers, preview = parse_xlsx_headers_preview(temp_path, preview_rows=6)

    if not headers:
        return render_template(
            "project/people_import_upload.html",
            active_project_id=project_id,
            project=project,
            error="Could not read headers from file.",
        ), 400

    required_columns = ['Name', 'Job Title', 'Role']
    optional_columns = []

    preview_data = {}
    for index, column in enumerate(headers):
        preview_data[column] = [row[index] for row in preview]

    return render_template("project/table_column_mapper.html", 
                           active_project_id=project_id,
                           table_type=table_type,
                           required_columns=required_columns,
                           optional_columns=optional_columns,
                           preview_data=preview_data,
                           temp_path=temp_path), 200


@DataBP.route('/<project_id>/<table_type>/columnmapper/commit', methods=['POST'])
def column_mapper_commit(project_id, table_type):
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

    # request form data from table_column_mapper will have entries
    # where key is "original_col_name=ORIGINAL_COLUMN_NAME" and the value is
    # the mapped column name

    # "original" refers to the name in the spreadsheet
    # "mapped" refers to the value we want to map it to
    original_to_mapped = {}
    for k, v in request.form.items():
        if k.startswith('original_col_name'):
            original_to_mapped[k.replace('original_col_name=', '')] = v
    mapped_to_original = {v: k for k, v in original_to_mapped.items()}

    def _idx_for(field_name: str):
        if field_name in mapped_to_original:
            selected = mapped_to_original[field_name]
            return header_to_idx.get(selected)
        else:
            return None


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
    

    #
    # People handler
    #
    name_i = _idx_for("Name")
    email_i = _idx_for("Email")
    phone_i = _idx_for("Phone")
    title_i = _idx_for("Job Title")
    role_level_i = _idx_for("Role")

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
