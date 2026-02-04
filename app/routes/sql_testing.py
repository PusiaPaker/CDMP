from flask import Blueprint, jsonify, render_template
from app.src.database import db
from app.tables.users import User

TestBP = Blueprint('test', __name__)

@TestBP.route('/get')
def getData():
    users = db.session.query(User).all()

    res = []
    for user in users:
        res.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "group_id": user.group_id
        })
    
    return render_template("demo_sql_test/list_users.html", dict_list=res), 200

@TestBP.route('/upload/<username>', methods=['GET'])
def uploadData(username: str):
    user = User(
        username = username,
        email = username + "@gmail.com",
        group_id = None,
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "group_id": user.group_id,
    }), 201

