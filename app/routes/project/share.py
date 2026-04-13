from flask import Blueprint, render_template, session, jsonify, url_for, redirect, request
from sqlalchemy import select, and_, update, values

from .project import ProjectBP
from app.core import db

from app.tables import Project, User, Role
from app.src.project.queries import get_users_from_project, user_is_project_owner, user_has_project_access



@ProjectBP.route('/<project_id>/share', methods=['GET', 'POST'])
def share(project_id):
    if not user_has_project_access(session['user_id'], project_id):
        return render_template("error/404.html"), 404

    project = db.session.get(Project, project_id)
    if not project:
        return render_template("error/404.html"), 404

    authorized_users = get_users_from_project(project_id)
    is_owner = user_is_project_owner(session["user_id"], project_id)

    def render(error=""):
        return render_template("project/share.html.j2", 
                authorized_users=authorized_users, 
                is_owner=is_owner,
                error=error,
                active_project=project, 
                active_project_id=project.id)


    if request.method == 'GET':
        return render()
    elif request.method == 'POST':
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        form_role = request.form.get("role", "viewer")

        user = None
        if email:
            user = db.session.query(User).filter_by(email=email).first()
        elif username:
            user = db.session.query(User).filter_by(username=username).first()

        if not user:
            return render("Error: User not found.")
        elif user.id == session['user_id']:
            return render("You shouldn't change your own permissions.")

        existing_role = db.session.query(Role).filter(
            and_(
                Role.user_id == user.id,
                Role.project_id == project_id
            )).first()

        if form_role == "remove":
            if existing_role:
                db.session.delete(existing_role)
            else:
                return render("Error: User not found.")
        else:
            if existing_role:
                db.session.execute(
                    update(Role)
                    .where(
                        and_(
                            Role.user_id == user.id,
                            Role.project_id == project.id
                        )
                    ).values(role=form_role)
                )
            else:
                new_role = Role(user_id=user.id, project_id=project_id, role=form_role)
                db.session.add(new_role)

        db.session.commit()    
        return redirect(url_for('project.share', project_id=project_id))
