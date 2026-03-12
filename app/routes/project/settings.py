from flask import render_template, redirect, url_for, jsonify, session, request

import uuid

from .project import ProjectBP
from app.src.project.queries import get_projects_for_user, user_is_project_owner, user_has_project_access

from app.core import db
from app.tables import Project, Role, ProjectPerson, File, TimelineEvent

@ProjectBP.route('/<project_id>/settings', methods=['GET'])
def settings(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    if not user_has_project_access(session["user_id"], project_id):
        return redirect(url_for('dashboard.get_dashboard_main'))

    is_owner = user_is_project_owner(session["user_id"], project_id)

    return render_template(
        "project/settings.html",
        active_project=project,
        active_project_id=project.id,
        is_owner=is_owner
    ), 200

@ProjectBP.route('/edit/<project_id>', methods=['GET', 'POST'])
def edit(project_id):
    if request.method == 'GET':
        project = db.session.get(Project, project_id)
        if not project:
            return render_template("error/404.html"), 404
        
        if not user_has_project_access(session["user_id"], project_id):
            return redirect(url_for('dashboard.get_dashboard_main'))

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

@ProjectBP.route('/<project_id>/delete')
def delete(project_id):
    if user_is_project_owner(session["user_id"], project_id):

        ### SOMEONE MAKE SURE THIS LOOKS RIGHT!!!
        ### Idk the difference between .query() and .execute() so IDK which to use.
        ### I believe this should work fine though. It deletes the appropriate roles, 
        ### I know that for a fact, so the rest /should/ work.

        proj = db.session.query(Project).filter_by(id=project_id).first()
        proj_people = db.session.query(ProjectPerson).filter_by(project_id=project_id).all()
        proj_roles = db.session.query(Role).filter_by(project_id=project_id).all()
        proj_files = db.session.query(File).filter_by(project_id=project_id).all()
        proj_timeline_events = db.session.query(TimelineEvent).filter_by(project_id=project_id).all()

        for proj_timeline_event in proj_timeline_events:
            db.session.delete(proj_timeline_event)
        for proj_file in proj_files:
            db.session.delete(proj_file)
        for proj_person in proj_people:
            db.session.delete(proj_person) 
        for proj_role in proj_roles:
            db.session.delete(proj_role)
        db.session.delete(proj)
        db.session.commit()

    # Redirect to dashboard either way since users should NOT be able
    # to execute this function if they're not the project owner (the 
    # button won't display for editors/viewers)
    return redirect(url_for("dashboard.get_dashboard_main"))
    


