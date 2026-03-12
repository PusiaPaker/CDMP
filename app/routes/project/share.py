from flask import Blueprint, render_template, session, jsonify
from app.tables import Project
from app.src.project.queries import get_users_from_project


@ProjectsBP.route('/<project_id>/share', methods=['GET', 'POST'])
def project_share(project_id):
    project = db.session.get(Project, project_id)

    authorized_users = get_users_from_project(project_id)

    if not project:
        return render_template("error/404.html"), 404

    if request.method == 'GET':
        return render_template("pages/project_share.html", 
            authorized_users=authorized_users, 
            active_project=project, 
            active_project_id=project.id)