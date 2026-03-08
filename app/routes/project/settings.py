from flask import render_template, redirect, url_for, jsonify, session, request

import uuid

from .project import ProjectBP
from app.src.project.queries import get_projects_for_user

from app.core import db
from app.tables import Project, Role

@ProjectBP.route('/<project_id>/settings', methods=['GET'])
def settings(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    return render_template(
        "project/settings.html",
        active_project=project,
        active_project_id=project.id,
    ), 200

@ProjectBP.route('/edit/<project_id>', methods=['GET', 'POST'])
def edit(project_id):
    if request.method == 'GET':
        project = db.session.get(Project, project_id)
        return render_template("project/project_add_data.html", active_project_id=project.id, active_project=project, status=None), 200

    elif request.method == 'POST':
        which_form = request.form.get('which_form', 'update_fields')

        if which_form == 'update_fields':
            project = db.session.get(Project, project_id)
            project.title = request.form['title']
            project.description = request.form['description']
            db.session.commit()
    
            # This should probably so that it redirect you to the just edited project
            return render_template("dashboard/home.html", dashboard_title='Hello, Username!', projects=get_projects_for_user(user_id=session["user_id"])), 200

        return redirect(url_for('project.edit', project_id=project_id))

@ProjectBP.route('/new', methods=['GET', 'POST'])
def create():
    user_id = session["user_id"]
    projects = get_projects_for_user(user_id)
    
    if request.method == 'GET':
        return render_template("project/create.html", projects=projects, status=None), 200
    elif request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        proj_id = str(uuid.uuid4())
        project = Project(id=proj_id, owner_id=user_id,title=title, description=description)
        db.session.add(project)

        r = Role(user_id = user_id, project_id = proj_id, role = 'owner')
        db.session.add(r)

        db.session.commit()
        projects = get_projects_for_user(user_id)

        return render_template('dashboard/home.html', projects=projects, status='success'), 200

@ProjectBP.route('/get')
def get_projects():
    proj = db.session.query(Project).all()

    out = {}
    for p in proj:
        out[p.title] = {'description': p.description, 'id': p.id}
    
    return jsonify(out), 200

