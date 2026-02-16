from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify
from app.src.database import db
from app.tables.projects import Project
from app.src.util_functions import get_all_projects

ProjectsBP = Blueprint('projects', __name__)

# @projectsBP.before_request
# def require_login():
#     if "user_id" not in session:
#         return redirect(url_for("authentication.login", next=request.path))

# TEMPORARY test project data
# will be injected into database when you try to access /projects/createdummies endpoint
dummy_data = {
    'Sherwin Williams DBMS Transition': '''This project involves migration Sherwin Williams\' customer service database from MongoDB to PostreSQL. Hired on June 12, expect contract to be ~6 months. Emergency contact at Sherwin: Timothy Harris 330 111 1111''',
    'Huntington Bank ATM API': '''Spending a lot of time digging into how their ATM stack is actually wired together, which is messier than it looks on paper. Talking with ops about weird edge cases (timeouts, partial transactions, logging gaps) and sketching a cleaner flow for updates and testing so releases don’t feel like mini heart attacks. The main aim right now is just making the system more predictable and less painful to maintain.''',
    'Diebold Nixdorf AI Chatbot': 'Focused on how the chatbot should behave in real situations instead of the idealized flows. Sitting in on support calls, noting common customer frustrations, and translating that into conversation logic that doesn’t feel robotic. Coordinating with the vendor on integrations and agent handoff. It’s still iterative, but early pilots show a drop in repetitive tickets.'
}

@ProjectsBP.route('/new', methods=['GET', 'POST'])
def create_project():
    if request.method == 'GET':
        return render_template("pages/project_create.html", projects=get_all_projects(), status=None), 200
    elif request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        project = Project(title=title, description=description)
        db.session.add(project)
        db.session.commit()

        return render_template('pages/project_create.html', projects=get_all_projects(), status='success'), 204

@ProjectsBP.route('/edit/<project_id>', methods=['GET', 'POST'])
def add_data_project(project_id):
    if request.method == 'GET':
        project = db.session.get(Project, project_id)

        return render_template("pages/project_add_data.html", projects=get_all_projects(), active_project=project, status=None), 200
    
    elif request.method == 'POST':
        project = db.session.get(Project, project_id)

        project.title = request.form['title']
        project.description = request.form['description']

        db.session.commit()

        # for now just redirect to main page after update is applied
        return render_template("dashboard/dashboard_overview.html", dashboard_title='Hello, Username!', projects=get_all_projects()), 200



@ProjectsBP.route('/createdummies')
def create_dummy_projects():
    proj = db.session.query(Project).filter_by(title=list(dummy_data.items())[0][0]).first()

    if not proj:
        for title, description in dummy_data.items():
            proj = Project(title = title, description = description)

            db.session.add(proj)
            db.session.commit()
    
    return '', 204

@ProjectsBP.route('/get')
def get_projects():
    proj = db.session.query(Project).all()

    out = {}
    for p in proj:
        out[p.title] = {'description': p.description, 'id': p.id}
    
    return jsonify(out), 200
