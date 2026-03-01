from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify
from app.src.database import db
from app.tables.projects import Project
from app.tables.roles import Role
from app.tables.files import File
from app.src.util_functions import get_projects_for_user
from werkzeug.utils import secure_filename
import os
from app.src.constants import ALLOWED_FILE_EXTENSIONS
import uuid

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
    user_id = session["user_id"]
    projects = get_projects_for_user(user_id)
    
    if request.method == 'GET':
        return render_template("pages/project_create.html", projects=projects, status=None), 200
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

        return render_template('dashboard/dashboard_overview.html', projects=projects, status='success'), 200

@ProjectsBP.route('/edit/<project_id>', methods=['GET', 'POST'])
def add_data_project(project_id):
    if request.method == 'GET':
        project = db.session.get(Project, project_id)

        return render_template("pages/project_add_data.html", active_project_id=project.id, active_project=project, status=None), 200
    
    elif request.method == 'POST':
        which_form = request.form['which_form']

        if which_form == 'update_fields':
            project = db.session.get(Project, project_id)

            project.title = request.form['title']
            project.description = request.form['description']

            db.session.commit()

            # for now just redirect to main page after update is applied
            return render_template("dashboard/dashboard_overview.html", dashboard_title='Hello, Username!', projects=get_projects_for_user(user_id=session["user_id"])), 200

        elif which_form == 'upload_documents':
            f = request.files['uploaded_file']
            if f.filename == '':
                # browser sends empty file if none was put in form
                # handle this here later
                # for now just take to 404
                return render_template("error/404.html"), 404
            
            # validate extension
            if f.filename.split('.')[-1] not in ALLOWED_FILE_EXTENSIONS:
                # forbidden file extension
                # we probably want an error page or error message pop up
                pass



            file_name = secure_filename(f.filename)

            # lets save to disk as id + extension
            temp_id = str(uuid.uuid4())
            extension = file_name.split('.')[-1]
            disk_file_name = f'{temp_id}.{extension}'

            f.save(os.path.join(os.getenv('FILE_UPLOAD_STORAGE_PATH'), disk_file_name))

            print(request.form)

            file_in_db = File(id=temp_id, project_id=project_id, 
                              file_name_original=file_name, 
                              file_name_disk=disk_file_name,
                              file_category=request.form['file_category'],
                              description=request.form['upload-description'])
            db.session.add(file_in_db)
            db.session.commit()

            return render_template("dashboard/dashboard_overview.html", dashboard_title='Hello, Username!', projects=get_projects_for_user(user_id=session["user_id"])), 200

        else:
            # error
            pass

@ProjectsBP.route('/createdummies')
def create_dummy_projects():
    proj = db.session.query(Project).filter_by(title=list(dummy_data.items())[0][0]).first()

    if not proj:
        for title, description in dummy_data.items():
            proj = Project(title = title, description = description, owner_id=session['user_id'])

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


# debug endpoint
@ProjectsBP.route('/getfiles/<project_id>')
def get_project_files_debug(project_id):
    files = db.session.query(File).filter(File.project_id == project_id).all()

    file_names = [{'file_name_original': f.file_name_original,
                   'file_name_disk': f.file_name_disk,
                   'file_category': f.file_category,
                   'description': f.description, 
                   'date': f.upload_date.date()} for f in files]
    
    return jsonify(file_names), 200