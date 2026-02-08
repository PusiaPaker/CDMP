from flask import Blueprint, render_template

DashBP= Blueprint('dashboard', __name__)

# temporary project id:name
projects = {'alpha': 'Project Alpha', 'beta': 'Project Beta', 'gamma': 'Project Gamma'}

@DashBP.route('/')
def get_dashboard_main():
    dashboard_title = 'All Projects View'

    return render_template("dashboard/dashboard_index.html", dashboard_title=dashboard_title, projects=projects), 200


# eventually replace this with some kind of project id? then get name and details from db
@DashBP.route('/<project_name>') 
def get_dashboard_project(project_name):
    return render_template("dashboard/dashboard_index.html", dashboard_title=projects[project_name], projects=projects), 200

