# https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/

from flask import Flask, Blueprint, render_template, redirect, request, session
from flask_session import Session

AuthBP = Blueprint('authentication', __name__)

@AuthBP.before_request
def checkAuth():
    if request.endpoint == "authentication.login":
        return
    if not session.get("id"):
        return redirect(url_for("authentication.login"))

@AuthBP.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["id"] = request.form.get("id")
        return redirect("/dashboard")
    return render_template("auth/login.html")

@AuthBP.route("/logout")
def logout():
    session["id"] = None
    return redirect("/login")

