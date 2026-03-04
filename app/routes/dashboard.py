from flask import Blueprint, render_template, session, redirect, request, url_for, abort, jsonify
from sqlalchemy import func, insert
from flask_session import Session
from sqlalchemy import select
from werkzeug.utils import secure_filename
import os
import uuid
import pandas as pd
import re

from app.tables.people import Person
from app.tables.project_people import ProjectPerson
from app.tables.users import User
from app.tables.files import File
from app.src.database import db
from app.tables.files import File
from app.tables.projects import Project
from app.src.util_functions import get_projects_for_user
from app.tables.people import Person
from app.tables.person_reports import PersonReport

DashBP= Blueprint('dashboard', __name__)


def _read_timeline_file_with_pandas(file_path: str):
    ext = file_path.split(".")[-1].lower()
    if ext == "csv":
        return pd.read_csv(file_path)
    if ext in ["xlsx", "xls"]:
        return pd.read_excel(file_path)
    raise ValueError("Unsupported file type.")


def _canonicalize_col_name(name: str):
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def _to_datetime_series(series: pd.Series):
    dt = pd.to_datetime(series, errors="coerce")

    numeric = pd.to_numeric(series, errors="coerce")
    valid_numeric = numeric.dropna()

    if not valid_numeric.empty:
        median = float(valid_numeric.median())
        # Excel serial dates are usually day counts in this rough range.
        if 20000 <= median <= 60000:
            excel_dt = pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")
            dt = dt.where(numeric.isna(), excel_dt)

    return dt


def _infer_timeline_columns(df: pd.DataFrame):
    if df.empty:
        raise ValueError("The uploaded file is empty.")

    normalized = {_canonicalize_col_name(c): c for c in df.columns}

    def _pick_exact(preferred: list[str]):
        for candidate in preferred:
            key = _canonicalize_col_name(candidate)
            if key in normalized:
                return normalized[key]
        return None

    def _pick_contains(required_terms: list[str]):
        for key, original in normalized.items():
            if all(term in key for term in required_terms):
                return original
        return None

    start_col = _pick_exact(["start_date", "start", "begin_date", "begin", "from", "date"])
    end_col = _pick_exact(["end_date", "end", "finish_date", "finish", "to", "due_date"])
    title_col = _pick_exact(["title", "task", "event", "milestone", "name", "summary", "description"])

    if not start_col:
        start_col = _pick_contains(["start", "date"]) or _pick_contains(["start"])
    if not end_col:
        end_col = _pick_contains(["end", "date"]) or _pick_contains(["finish"])
    if not title_col:
        title_col = _pick_contains(["task"]) or _pick_contains(["event"]) or _pick_contains(["name"])

    if not start_col:
        for col in df.columns:
            series = df[col]
            non_null_count = int(series.notna().sum())
            if non_null_count == 0:
                continue
            parsed = _to_datetime_series(series)
            if (int(parsed.notna().sum()) / non_null_count) >= 0.6:
                start_col = col
                break

    if not end_col and start_col:
        for col in df.columns:
            if col == start_col:
                continue
            series = df[col]
            non_null_count = int(series.notna().sum())
            if non_null_count == 0:
                continue
            parsed = _to_datetime_series(series)
            if (int(parsed.notna().sum()) / non_null_count) >= 0.6:
                end_col = col
                break

    if not title_col:
        for col in df.columns:
            if col not in [start_col, end_col]:
                title_col = col
                break

    if not start_col:
        raise ValueError("Could not infer a start-date column. Add a column like start_date/date.")

    return title_col, start_col, end_col


def _build_timeline_events(df: pd.DataFrame, title_col: str | None, start_col: str, end_col: str | None):
    starts = _to_datetime_series(df[start_col])
    ends = _to_datetime_series(df[end_col]) if end_col else None

    if title_col:
        titles = df[title_col].fillna("").astype(str).str.strip()
    else:
        titles = pd.Series([""] * len(df))

    events = []
    for idx in range(len(df)):
        start_ts = starts.iloc[idx]
        if pd.isna(start_ts):
            if ends is not None and not pd.isna(ends.iloc[idx]):
                start_ts = ends.iloc[idx]
            else:
                continue

        title = titles.iloc[idx] if idx < len(titles) else ""
        if not title:
            title = f"Event {idx + 1}"

        end_iso = None
        if ends is not None:
            end_ts = ends.iloc[idx]
            if not pd.isna(end_ts):
                if end_ts < start_ts:
                    end_ts = start_ts
                if end_ts != start_ts:
                    end_iso = end_ts.isoformat()

        events.append(
            {
                "id": idx + 1,
                "content": title,
                "start": start_ts.isoformat(),
                "end": end_iso,
            }
        )

    if not events:
        raise ValueError("No valid timeline events found. Check your date columns.")

    return events

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route('/')
def get_dashboard_main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    dashboard_title = f'Welcome, {username}'
    description = "Here are your projects."

    return render_template(
        "dashboard/dashboard_overview.html",
        dashboard_title=dashboard_title,
        description=description,
        projects=projects,
    ), 200

@DashBP.route('/<project_id>/')
def get_dashboard_project_home(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    people_rows = (
        db.session.execute(
            select(Person, ProjectPerson)
            .join(ProjectPerson, ProjectPerson.person_id == Person.id)
            .where(ProjectPerson.project_id == project_id)
            .order_by(Person.name.asc())
        )
        .all()
    )

    recent_files = (
        db.session.execute(
            select(File)
            .where(File.project_id == project_id)
            .order_by(File.upload_date.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )

    return render_template(
        "dashboard/dashboard_project_home.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        recent_files=recent_files,
    ), 200

@DashBP.route('/<project_id>/visualizations/') 
def get_dashboard_project_visualizations(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    return render_template(
        "dashboard/dashboard_visualizations.html",
        project=project,
        active_project_id=project.id
    ), 200


@DashBP.route('/<project_id>/timeline/', methods=['GET', 'POST'])
def get_dashboard_project_timeline(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    if request.method == "GET":
        return render_template(
            "dashboard/dashboard_timeline.html",
            project=project,
            active_project_id=project.id,
            timeline_events=[],
            timeline_meta=None,
            error=None,
            success=None,
        ), 200

    f = request.files.get("uploaded_file")
    configured_root = os.getenv("FILE_UPLOAD_STORAGE_PATH", "").strip()
    if configured_root:
        destination_dir = os.path.join(configured_root, "timeline_uploads", project_id)
    else:
        destination_dir = os.path.join(os.getcwd(), "instance", "timeline_uploads", project_id)

    if not f or not f.filename:
        return render_template(
            "dashboard/dashboard_timeline.html",
            project=project,
            active_project_id=project.id,
            timeline_events=[],
            timeline_meta=None,
            error="Please choose a CSV or Excel file.",
            success=None,
        ), 400

    ext = f.filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx", "xls"]:
        return render_template(
            "dashboard/dashboard_timeline.html",
            project=project,
            active_project_id=project.id,
            timeline_events=[],
            timeline_meta=None,
            error="Only .csv, .xlsx, and .xls files are supported.",
            success=None,
        ), 400

    os.makedirs(destination_dir, exist_ok=True)

    original_name = secure_filename(f.filename)
    disk_name = f"{uuid.uuid4()}.{ext}"
    disk_path = os.path.join(destination_dir, disk_name)
    f.save(disk_path)

    try:
        df = _read_timeline_file_with_pandas(disk_path)
        title_col, start_col, end_col = _infer_timeline_columns(df)
        events = _build_timeline_events(df, title_col, start_col, end_col)

        meta = {
            "rows_total": int(len(df.index)),
            "events_total": int(len(events)),
            "title_col": title_col or "(auto-generated)",
            "start_col": start_col,
            "end_col": end_col or "(none)",
            "file_path": disk_path,
        }
    except Exception as exc:
        return render_template(
            "dashboard/dashboard_timeline.html",
            project=project,
            active_project_id=project.id,
            timeline_events=[],
            timeline_meta=None,
            error=f"Could not build timeline: {exc}",
            success=None,
        ), 400

    return render_template(
        "dashboard/dashboard_timeline.html",
        project=project,
        active_project_id=project.id,
        timeline_events=events,
        timeline_meta=meta,
        error=None,
        success="File uploaded and timeline generated successfully.",
    ), 200


@DashBP.route('/<project_id>/people/')
def get_dashboard_project_people(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    xlsx_files = db.session.query(File).filter(
        File.project_id == project_id,
        func.lower(File.file_name_original).like('%.xlsx')
    ).order_by(File.upload_date.desc()).all()
    
    # reporting_people = [
    #     {"id": "person_1", "name": "Bryan Coblentz", "title": "Project Manager"},
    #     {"id": "person_2", "name": "Kevin Hare", "title": "Tech Lead"},
    #     {"id": "person_3", "name": "Matt Troyer", "title": "CEO"},
    #     {"id": "person_4", "name": "Jamie Coblentz", "title": "Software Engineer"},
    #     {"id": "person_5", "name": "Merl Coblentz", "title": "Software Engineer"},
    #     {"id": "person_6", "name": "Traci Miller", "title": "Software Engineer"},
    #     {"id": "person_7", "name": "Joel Coblentz", "title": "Product Designer"},
    #     {"id": "person_8", "name": "Joe Yoder", "title": "UX Desiner"},
    #     {"id": "person_9", "name": "Teresa Bonifant", "title": "Software Engineer"},
    #     {"id": "person_10", "name": "Darrin Hess", "title": "Consulting"},
    # ]


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
    
    return render_template(
        "dashboard/dashboard_people.html",
        project=project,
        active_project_id=project.id,
        people_rows=people_rows,
        reporting_links=reporting_links
        ), 200

@DashBP.route('/<project_id>/people/updatematrix', methods=['POST'])
def update_reporting_matrix(project_id):
    payload = request.get_json()

    person_id = payload["person_id"]
    manager_id = payload["manager_id"]
    checked = payload["checked"]

    is_checked = str(checked).lower() == "true" if isinstance(checked, str) else bool(checked)

    if is_checked:
        db.session.execute(
            insert(PersonReport)
            .values(person_id=person_id, reports_to_id=manager_id)
        )
    else:
        db.session.query(PersonReport).filter(
            PersonReport.person_id == person_id,
            PersonReport.reports_to_id == manager_id
        ).delete()

    db.session.commit()

    return jsonify({
        "person_id": person_id,
        "manager_id": manager_id,
        "checked": is_checked
    }), 200
