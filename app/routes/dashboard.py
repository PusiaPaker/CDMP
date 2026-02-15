from flask import Blueprint, render_template, session, redirect, request, url_for
from app.src.database import db
from app.tables.projects import Project

DashBP= Blueprint('dashboard', __name__)

# temporary project id:name
# first one should always be add project
# projects = {'_add_button': 'Add Project', 'alpha': 'Project Alpha',
#              'beta': 'Project Beta', 'gamma': 'Project Gamma'}

def get_all_projects():
    '''
    Retrieve all projects from db
    returns a dictionary where keys are project ids, and each value holds the title and description
    '''

    projects = db.session.query(Project).all()

    result = {}
    for project in projects:
        result[project.id] = {'description': project.description, 'title': project.title}

    return result


@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))


@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'All Projects View'

    projects = get_all_projects()

    return render_template("dashboard/dashboard_index.html", dashboard_title=dashboard_title, projects=projects), 200


# eventually replace this with some kind of project id? then get name and details from db
@DashBP.route('/<project_id>') 
def get_dashboard_project(project_id):
    project = db.session.get(Project, project_id)

    if not project:
        # TODO: project not found page
        pass

    projects = get_all_projects()

    return render_template("dashboard/dashboard_index.html", dashboard_title=project.title, description=project.description,
                            projects=projects, active_project_id=project.id), 200

