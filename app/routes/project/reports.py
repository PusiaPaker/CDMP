import os
import uuid

from sqlalchemy import select
from flask import render_template, abort, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename

from app.core import db
from app.src.user_display import get_user_display_name
from app.src.project.queries import user_has_project_access, user_can_edit_project
from app.tables import Project, User, File

from .project import ProjectBP
from app.src.project.reports import *

@ProjectBP.route("/<project_id>/reports/")
def reports(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    recent_saved_reports = (
        db.session.execute(
            select(File)
            .where(File.project_id == project_id)
            .where(File.description == "Auto-generated project report")
            .order_by(File.upload_date.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    return render_template(
        "project/reports.html.j2",
        project=project,
        active_project_id=project.id,
        recent_saved_reports=recent_saved_reports,
        can_edit_project=user_can_edit_project(session["user_id"], project_id),
    ), 200


@ProjectBP.route("/<project_id>/reports/download/")
def download_report(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    user = db.session.get(User, session.get("user_id"))
    
    return send_file(
        generate_report_pdf(project, get_user_display_name(user, default="Unknown")),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=get_report_file_name(project.title),
    )


@ProjectBP.route("/<project_id>/reports/save/")
def save_report_to_files(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if not user_can_edit_project(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    user = db.session.get(User, session.get("user_id"))

    report_pdf = generate_report_pdf(project, get_user_display_name(user, default="Unknown"))
    original_file_name = secure_filename(get_report_file_name(project.title))

    temp_id = str(uuid.uuid4())
    disk_file_name = f"{temp_id}.pdf"

    storage_dir = os.getenv("FILE_UPLOAD_STORAGE_PATH")
    os.makedirs(storage_dir, exist_ok=True)

    with open(os.path.join(storage_dir, disk_file_name), "wb") as f:
        f.write(report_pdf.getvalue())

    file_in_db = File(
        id=temp_id,
        project_id=project_id,
        file_name_original=original_file_name,
        file_name_disk=disk_file_name,
        file_category="unspecified",
        description="Auto-generated project report",
    )
    db.session.add(file_in_db)
    db.session.commit()

    return redirect(url_for("project.file_list", project_id=project_id))
