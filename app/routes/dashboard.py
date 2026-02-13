from flask import Blueprint, render_template, session, redirect, request, url_for

DashBP= Blueprint('dashboard', __name__)

# temporary project id:name
# first one should always be add project
projects = {'_add_button': 'Add Project', 'alpha': 'Project Alpha',
             'beta': 'Project Beta', 'gamma': 'Project Gamma'}

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))


@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'All Projects View'

    return render_template("dashboard/dashboard_index.html", dashboard_title=dashboard_title, projects=projects), 200


# eventually replace this with some kind of project id? then get name and details from db
@DashBP.route('/<project_name>') 
def get_dashboard_project(project_name):
    return render_template("dashboard/dashboard_index.html", dashboard_title=projects[project_name], projects=projects), 200

