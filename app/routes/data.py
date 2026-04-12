from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify, abort, flash
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

TABLE_TYPE_REDIRECTS = {
    "people": "project.people",
    "timeline": "project.calendar",
    "expenses": "project.finance",
}

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
            "project/upload.html.j2",
            active_project_id=project_id,
            project=project,
            table_type=table_type,
            back_endpoint=TABLE_TYPE_REDIRECTS.get(table_type, "project.home"),
        ), 200

    f = request.files.get("file")
    if not f or not f.filename:
        return render_template(
            "project/upload.html.j2",
            active_project_id=project_id,
            project=project,
            error="Please choose a file.",
            table_type=table_type,
            back_endpoint=TABLE_TYPE_REDIRECTS.get(table_type, "project.home"),
        ), 400

    ext = f.filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx"]:
        return render_template(
            "project/upload.html.j2",
            active_project_id=project_id,
            project=project,
            error="Only .csv or .xlsx is supported.",
            table_type=table_type,
            back_endpoint=TABLE_TYPE_REDIRECTS.get(table_type, "project.home"),
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
            "project/upload.html.j2",
            active_project_id=project_id,
            project=project,
            error="Could not read headers from file.",
            table_type=table_type,
            back_endpoint=TABLE_TYPE_REDIRECTS.get(table_type, "project.home"),
        ), 400

    tt_cols = table_type_columns[table_type]
    required_columns, optional_columns = tt_cols['required'], tt_cols['optional']

    preview_data = {}
    for index, column in enumerate(headers):
        preview_data[column] = [row[index] for row in preview]

    return render_template("project/column_mapper.html.j2", 
                           active_project_id=project_id,
                           table_type=table_type,
                           required_columns=required_columns,
                           optional_columns=optional_columns,
                           preview_data=preview_data,
                           temp_path=temp_path), 200


@DataBP.route('/<project_id>/<table_type>/columnmapper/commit', methods=['POST'])
def column_mapper_commit(project_id, table_type):
    error = None
    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/404.html"), 404

    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    temp_path = request.form.get("temp_path", "")
    if not temp_path or not os.path.exists(temp_path):
        return render_template("error/404.html"), 404
    
    required_columns, optional_columns = (table_type_columns[table_type]['required'],
                                           table_type_columns[table_type]['optional'])


    # check if two or more columns map to same value
    map_targets = [v for k, v in request.form.items() if (k.startswith('original_col_name') and (v != ''))]
    if len(map_targets) != len(set(map_targets)):
        error = 'Two or more columns cannot map to the same value.'

    # check if any of the required columns are missing 
    required_col_present = {colname:False for colname in required_columns}
    for _, map_target in request.form.items():
        if map_target in required_columns:
            required_col_present[map_target] = True
    if False in required_col_present.values():
        missing = [c for c in required_col_present if not required_col_present[c]]
        error = f'One or more required columns are missing: {missing}'
        

    ext = temp_path.split(".")[-1].lower()
    if ext == "csv":
        headers, rows = read_all_csv_rows(temp_path)
    else:
        headers, rows = read_all_xlsx_rows(temp_path)

    if error is not None:
        preview_data = {}
        for index, column in enumerate(headers):
            preview_data[column] = [row[index] for row in rows[:6]]

        return render_template("project/column_mapper.html.j2", 
                           active_project_id=project_id,
                           table_type=table_type,
                           required_columns=required_columns,
                           optional_columns=optional_columns,
                           preview_data=preview_data,
                           temp_path=temp_path,
                           error_message=error), 200


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

    header_to_idx = {h: i for i, h in enumerate(headers)}
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
        commit_status = people_mapping_handler(project_id, rows, mapped_to_index)
        flash(
            {
                "title": "People data inserted",
                "body": "The uploaded spreadsheet was processed and the project stakeholder data was updated.",
                "created": commit_status["created"],
                "skipped": commit_status["skipped"],
            },
            "success",
        )
        return redirect(url_for("project.people", project_id=project_id))

    elif table_type == 'timeline':
        commit_status = events_mapping_handler(project_id, rows, mapped_to_index)
        flash(
            {
                "title": "Timeline data inserted",
                "body": "The uploaded spreadsheet was processed and the project timeline was updated.",
                "created": commit_status["created"],
                "skipped": commit_status["skipped"],
            },
            "success",
        )
        return redirect(url_for("project.calendar", project_id=project_id))

    elif table_type == 'expenses':
        commit_status = expenses_mapping_handler(project_id, rows, mapped_to_index)
        flash(
            {
                "title": "Expense data inserted",
                "body": "The uploaded spreadsheet was processed and the project finance data was updated.",
                "created": commit_status["created"],
                "skipped": commit_status["skipped"],
            },
            "success",
        )
        return redirect(url_for("project.finance", project_id=project_id, tab="expenses"))
