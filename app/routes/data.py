from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify, abort
from sqlalchemy import select, exists, and_, insert
import pandas as pd
import os
import uuid
from datetime import datetime

from app.core import db
from app.tables import Project, ProjectPerson, Person, TimelineEvent

from app.src.project.files import path_to_file_from_disk
from .project import ProjectBP
from app.src.project.queries import user_has_project_access
from app.src.project.files import parse_csv_headers_preview, parse_xlsx_headers_preview, read_all_csv_rows, read_all_xlsx_rows
from app.src.constants import table_type_columns
from app.src.project.mapper import *

from collections import defaultdict

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
            "project/generic_import_upload.html",
            active_project_id=project_id,
            project=project,
            table_type=table_type
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

    tt_cols = table_type_columns[table_type]
    required_columns, optional_columns = tt_cols['required'], tt_cols['optional']

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
    print(project_id)
    print(session)
    print(request.form.get("temp_path", ""))
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

    mapped_to_index = {}
    for k, v in mapped_to_original.items():
        mapped_to_index[k] = header_to_idx[v]

    mapped_to_index = defaultdict(lambda: None, mapped_to_index)

    try:
        os.remove(temp_path)
    except OSError:
        pass

    # redirect to mapping handlers for each table type to save data in DB
    if table_type == 'people':
        people_mapping_handler(project_id, rows, mapped_to_index)
        return redirect(url_for("project.people", project_id=project_id))

    elif table_type == 'timeline':
        events_mapping_handler(project_id, rows, mapped_to_index)
        return redirect(url_for("project.timeline", project_id=project_id))