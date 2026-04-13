from decimal import Decimal, InvalidOperation

import os

from flask import current_app, render_template, redirect, url_for, jsonify, session, request

import uuid

from .project import ProjectBP
from app.src.project.queries import get_projects_for_user, user_is_project_owner, user_has_project_access, user_can_edit_project

from app.core import db
from app.tables import Expense, Project, Role, ProjectPerson, File, TimelineEvent


def _parse_budget_amount(raw_value):
    value = (raw_value or "").strip()
    if value == "":
        return None

    budget_amount = Decimal(value)
    if budget_amount < 0:
        raise InvalidOperation

    return budget_amount


def _delete_project_data(project_id):
    project_people = db.session.query(ProjectPerson).filter_by(project_id=project_id).all()
    project_files = db.session.query(File).filter_by(project_id=project_id).all()
    project_expenses = db.session.query(Expense).filter_by(project_id=project_id).all()
    project_timeline_events = db.session.query(TimelineEvent).filter_by(project_id=project_id).all()
    storage_dir = current_app.config.get("UPLOAD_FOLDER")

    for project_timeline_event in project_timeline_events:
        db.session.delete(project_timeline_event)
    for project_expense in project_expenses:
        db.session.delete(project_expense)
    for project_file in project_files:
        if storage_dir:
            file_path = os.path.join(storage_dir, project_file.file_name_disk)
            if os.path.exists(file_path):
                os.remove(file_path)
        db.session.delete(project_file)
    for project_person in project_people:
        db.session.delete(project_person)


def _delete_project(project_id):
    project = db.session.query(Project).filter_by(id=project_id).first()
    if not project:
        return

    project_roles = db.session.query(Role).filter_by(project_id=project_id).all()

    _delete_project_data(project_id)

    for project_role in project_roles:
        db.session.delete(project_role)
    db.session.delete(project)
    db.session.commit()

@ProjectBP.route('/<project_id>/settings', methods=['GET'])
def settings(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    is_owner = user_is_project_owner(session["user_id"], project_id)
    can_edit_project = user_can_edit_project(session["user_id"], project_id)

    return render_template(
        "project/settings.html.j2",
        project=project,
        active_project_id=project.id,
        is_owner=is_owner,
        can_edit_project=can_edit_project,
    ), 200

@ProjectBP.route('/edit/<project_id>', methods=['GET', 'POST'])
def edit(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if not user_can_edit_project(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if request.method == 'GET':
        return render_template(
            "project/project_add_data.html.j2",
            project=project,
            active_project_id=project.id,
            form_title=f'Edit "{project.title}"',
            form_subtitle="Update the project name, description, and optional budget.",
            submit_label="Save Changes",
            form_action=url_for('project.edit', project_id=project.id),
            cancel_url=url_for('project.home', project_id=project.id),
            status=None,
            error=None
        ), 200

    try:
        budget_amount = _parse_budget_amount(request.form.get('budget_amount', ''))
    except InvalidOperation:
        return render_template(
            "project/project_add_data.html.j2",
            project=project,
            active_project_id=project.id,
            form_title=f'Edit "{project.title}"',
            form_subtitle="Update the project name, description, and optional budget.",
            submit_label="Save Changes",
            form_action=url_for('project.edit', project_id=project.id),
            cancel_url=url_for('project.home', project_id=project.id),
            status=None,
            error="Budget amount must be a valid non-negative number.",
        ), 400

    project.title = request.form['title']
    project.description = request.form['description']
    project.budget_amount = budget_amount
    db.session.commit()

    return redirect(url_for('project.home', project_id=project.id))

@ProjectBP.route('/new', methods=['GET', 'POST'])
def create():
    user_id = session["user_id"]

    if request.method == 'GET':
        return render_template(
            "project/create.html.j2",
            project=None,
            form_title="Create Project",
            form_subtitle="Start a new project workspace with an optional budget.",
            submit_label="Create Project",
            form_action=url_for('project.create'),
            cancel_url=url_for('dashboard.main'),
            status=None,
            error=None
        ), 200

    title = request.form['title']
    description = request.form['description']
    try:
        budget_amount = _parse_budget_amount(request.form.get('budget_amount', ''))
    except InvalidOperation:
        return render_template(
            "project/create.html.j2",
            project=None,
            form_title="Create Project",
            form_subtitle="Start a new project workspace with an optional budget.",
            submit_label="Create Project",
            form_action=url_for('project.create'),
            cancel_url=url_for('dashboard.main'),
            status=None,
            error="Budget amount must be a valid non-negative number.",
        ), 400

    proj_id = str(uuid.uuid4())
    project = Project(
        id=proj_id,
        owner_id=user_id,
        title=title,
        description=description,
        budget_amount=budget_amount,
    )
    db.session.add(project)

    owner_role = Role(
        user_id=user_id,
        project_id=proj_id,
        role='owner'
    )
    db.session.add(owner_role)

    db.session.commit()

    return redirect(url_for('project.home', project_id=proj_id))

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
        _delete_project(project_id)

    # Redirect to dashboard either way since users should NOT be able
    # to execute this function if they're not the project owner (the 
    # button won't display for editors/viewers)
    return redirect(url_for("dashboard.main"))
    
