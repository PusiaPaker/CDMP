from flask import Blueprint, render_template, session, redirect, request, url_for
from app.src.database import db
from app.tables.projects import Project
from app.src.util_functions import get_all_projects

DashBP= Blueprint('dashboard', __name__)
"""
@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))
"""

@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'Welcome, Username!'

    projects = get_all_projects()

    return render_template("dashboard/dashboard_overview.html", dashboard_title=dashboard_title, projects=projects), 200


# eventually replace this with some kind of project id? then get name and details from db
@DashBP.route('/<project_id>') 
def get_dashboard_project(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        # TODO: project not found page
        pass

    projects = get_all_projects()

    """
    return render_template("dashboard/dashboard_project.html", dashboard_title=project.title, description=project.description,
                            projects=projects, active_project_id=project.id), 200
    """
    return render_template("dashboard/dashboard_project.html", project=project, projects=projects, active_project_id=project.id), 200

