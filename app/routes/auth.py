from flask import Blueprint, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app.core import db
from app.tables import User

AuthBP = Blueprint('authentication', __name__)


def _is_strong_password(password: str) -> bool:
    return (
        len(password) >= 10
        and any(character.isdigit() for character in password)
        and any(character.islower() for character in password)
        and any(character.isupper() for character in password)
        and any(not character.isalnum() for character in password)
    )

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
        return redirect(url_for("dashboard.main"))

    return render_template("auth/login.html")

@AuthBP.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()

        if not full_name:
            return render_template("auth/register.html", error="Full name is required."), 400
        if not _is_strong_password(password):
            return render_template(
                "auth/register.html",
                error="Password must be 10+ characters and include uppercase, lowercase, number, and special character.",
            ), 400

        user = db.session.query(User).filter_by(username=username).first()
        if user:
            return render_template("auth/register.html", error="Username is taken."), 401
        

        new_user = User(
            username=username,
            full_name=full_name,
            password=generate_password_hash(password),
            email=email,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("authentication.login"))

    return render_template("auth/register.html")
