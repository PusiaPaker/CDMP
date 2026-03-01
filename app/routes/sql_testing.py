from flask import Blueprint, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from app.src.database import db
from app.tables.users import User

DebugBP = Blueprint('debug', __name__)

@DebugBP.route('/get')
def getData():
    users = db.session.query(User).all()

    res = []
    for user in users:
        res.append({
            "id": user.id,
            "username": user.username,
            "password": user.password,
            "email": user.email,
        })
    
    return render_template("demo_sql_test/list_users.html", dict_list=res), 200

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

