from flask import Blueprint, render_template, session, redirect, request, url_for, abort
from app.src.database import db
from app.tables.projects import Project
from app.src.util_functions import get_all_projects

DashBP= Blueprint('dashboard', __name__)

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'Welcome, Username!'

    projects = get_all_projects()

    return render_template("dashboard/dashboard_overview.html", dashboard_title=dashboard_title, projects=projects), 200


@DashBP.route('/<project_id>/visualizations/') 
def get_dashboard_project_visualizations(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        return abort(404)

    return render_template("dashboard/dashboard_visualizations.html", project=project, active_project_id=project.id), 200


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

    return render_template("dashboard/dashboard_people.html", project=project, active_project_id=project.id), 200
