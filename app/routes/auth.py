# https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/

from flask import Flask, Blueprint, render_template, redirect, request, session, make_response, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash


from app.src.database import db
from app.tables.users import User

AuthBP = Blueprint('authentication', __name__)

@AuthBP.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("authentication.login"))

@AuthBP.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.session.query(User).filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template("auth/login.html", error="Bad username or password"), 401

        remember = request.form.get("remember_me") == "true"
        session.permanent = remember

        session["user_id"] = user.id

        next_url = request.args.get("next")
        return redirect(next_url or url_for("dashboard.get_dashboard_main"))

    return render_template("auth/login.html")
