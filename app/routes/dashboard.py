from flask import Blueprint, render_template, session, redirect, request, url_for, abort, jsonify
from sqlalchemy import func, insert
from flask_session import Session

from app.src.database import db
from app.tables.files import File
from app.tables.projects import Project
from app.src.util_functions import get_projects_for_user
from app.tables.people import Person
from app.tables.person_reports import PersonReport

DashBP= Blueprint('dashboard', __name__)

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'Welcome, Username!'

    user_id = session["user_id"]
    projects = get_projects_for_user(user_id)

    return render_template("dashboard/dashboard_overview.html", dashboard_title=dashboard_title, projects=projects), 200


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


@DashBP.route('/<project_id>/timeline/') 
def get_dashboard_project_timeline(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    return render_template("dashboard/dashboard_timeline.html", project=project, active_project_id=project.id), 200


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

    people = db.session.query(Person).filter(Person.project_id == project_id).all()    

    reporting_edges = (
        db.session.query(PersonReport.person_id, PersonReport.reports_to_id)
        .join(Person, Person.id == PersonReport.person_id)
        .filter(Person.project_id == project_id)
        .all()
    )
    reporting_links = {f"{person_id}:{reports_to_id}" for person_id, reports_to_id in reporting_edges}

    return render_template("dashboard/dashboard_people.html", project=project,
                            active_project_id=project.id,
                            xlsx_files=xlsx_files,
                            reporting_people=people,
                            reporting_links=reporting_links), 200


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
