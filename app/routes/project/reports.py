from flask import render_template, abort, send_file

from app.core import db
from app.tables import Project

from .project import ProjectBP
from app.src.project.reports import *

@ProjectBP.route("/<project_id>/reports/")
def reports(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    return render_template(
        "project/reports.html.j2",
        project=project
    ), 200


@ProjectBP.route("/<project_id>/reports/download/")
def download_report(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)
    
    return send_file(
        generate_report_pdf(project),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=get_report_file_name(project.title),
    )
