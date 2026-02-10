# https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/

from flask import Flask, Blueprint, render_template, redirect, request, session, make_response, url_for
from flask_session import Session

AuthBP = Blueprint('authentication', __name__)

@AuthBP.route('/logout')
def logout():
    session.pop("id", None)
    
    resp = make_response(redirect("/login"))
    resp.set_cookie('remember_me', '', max_age=0)  # Delete cookie
    
    return resp

@AuthBP.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        remember_token = request.cookies.get('remember_me')
        if remember_token:
            session["id"] = remember_token
            return redirect("/dashboard")
    
    if request.method == "POST":
        user_id = request.form.get("id")
        remember = request.form.get("remember_me") == "true"
        
        session["id"] = user_id
        
        resp = make_response(redirect("/dashboard"))
        
        if remember:
            resp.set_cookie(
                'remember_me',
                user_id,
                max_age=30*24*60*60,
                secure=False,
                httponly=True,
                samesite='Lax'
            )
        return resp
    
    return render_template("auth/login.html")