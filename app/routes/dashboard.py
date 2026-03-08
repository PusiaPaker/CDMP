from flask import Blueprint, redirect, render_template, request, session, url_for

from app.src.project.queries import get_projects_for_user

from app.core import db
from app.tables import User

DashBP = Blueprint("dashboard", __name__)

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route("/")
def get_dashboard_main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    dashboard_title = f"Welcome, {username}"
    description = "Here are your projects."

    return render_template(
        "dashboard/home.html",
        dashboard_title=dashboard_title,
        description=description,
        projects=projects,
    ), 200
