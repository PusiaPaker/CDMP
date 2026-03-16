from flask import Blueprint, jsonify, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app.core import db
from app.tables import User, Role
from app.populate.users import populateUsers
from app.populate.projects import populateProjects
from app.populate.roles import populateRoles

DebugBP = Blueprint('debug', __name__)

@DebugBP.route('/get/users')
def getUsers():
    users = db.session.query(User).all()

    res = []
    for user in users:
        res.append({
            "id": user.id,
            "username": user.username,
            "password": user.password,
            "email": user.email,
        })
    
    return render_template("debug/list_data.html", data_type="Users", dict_list=res), 200

@DebugBP.route('/get/roles')
def getRoles():
    roles = db.session.query(Role).all()

    res = []
    for role in roles:
        res.append({
            "id": role.id,
            "user_id": role.user_id,
            "project_id": role.project_id,
            "role": role.role
        })

    return render_template('debug/list_data.html', data_type="Roles", dict_list=res), 200

@DebugBP.route('/populate')
def populateDatabase():
    populateUsers()
    populateProjects()
    populateRoles()

    return redirect(url_for('debug.getUsers'))



@DebugBP.route('/register/<username>/<password>', methods=['GET'])
def registerUser(username: str, password: str):
    user = User(
        username = username,
        password = generate_password_hash(password),
        email = username + "@gmail.com",
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "password": user.password,
        "email": user.email,
    }), 201

@DebugBP.route('/delete/<username>', methods=['GET'])
def deleteUser(username: str):
    user = db.session.query(User).filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": f"user '{username}' deleted"
    }), 200

