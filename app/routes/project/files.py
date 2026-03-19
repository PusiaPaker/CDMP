from werkzeug.utils import secure_filename
from flask import render_template, redirect, request, url_for, jsonify

import uuid
import os

from .project import ProjectBP
from app.tables import File, Project
from app.core import db
from app.src.project.queries import get_project_workspace_context

from app.src.constants import ALLOWED_FILE_EXTENSIONS

@ProjectBP.route('/<project_id>/files', methods=['GET'])
def file_list(project_id):
    files = db.session.query(File).filter(File.project_id == project_id).order_by(File.upload_date.desc()).all()
    project = db.session.get(Project, project_id)
    workspace_context = get_project_workspace_context(project_id)
    return render_template(
        "project/files.html",
        project=project,
        active_project_id=project.id,
        files=files,
        project_tab="files",
        **workspace_context,
    ), 200


@ProjectBP.route('/<project_id>/files/upload', methods=['GET', 'POST'])
def file_upload(project_id):
    project = db.session.get(Project, project_id)
    workspace_context = get_project_workspace_context(project_id)

    if request.method == 'GET':
        return render_template(
            "project/upload.html",
            project=project,
            active_project_id=project.id,
            status=None,
            project_tab="upload",
            **workspace_context,
        ), 200

    f = request.files.get('uploaded_file')
    if not f or f.filename == '':
        return render_template("error/404.html"), 404

    ext = f.filename.split('.')[-1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return render_template(
            "project/upload.html",
            project=project,
            active_project_id=project.id,
            error="Invalid extension",
            project_tab="upload",
            **workspace_context,
        ), 400

    file_name = secure_filename(f.filename)

    temp_id = str(uuid.uuid4())
    disk_file_name = f'{temp_id}.{ext}'

    f.save(os.path.join(os.getenv('FILE_UPLOAD_STORAGE_PATH'), disk_file_name))

    file_in_db = File(
        id=temp_id,
        project_id=project_id,
        file_name_original=file_name,
        file_name_disk=disk_file_name,
        file_category=request.form.get('file_category', 'unspecified'),
        description=request.form.get('upload-description', ''),
    )
    db.session.add(file_in_db)
    db.session.commit()

    return redirect(url_for('project.file_list', project_id=project_id))


# debug endpoint
@ProjectBP.route('/getfiles/<project_id>')
def get_project_files_debug(project_id):
    files = db.session.query(File).filter(File.project_id == project_id).all()

    file_names = [{'file_name_original': f.file_name_original,
                   'file_name_disk': f.file_name_disk,
                   'file_category': f.file_category,
                   'description': f.description, 
                   'date': f.upload_date.date()} for f in files]
    
    return jsonify(file_names), 200
