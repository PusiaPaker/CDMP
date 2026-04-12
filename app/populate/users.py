from werkzeug.security import generate_password_hash
from sqlalchemy import select, exists

from app.core import db
from app.tables import User

def checkUserInDatabase(username) -> bool:
    return db.session.execute(select(
        exists().where(User.username == username)
    )).scalar()

def createUser(name, passwd, email=None, full_name=None) -> User | None:
    if not checkUserInDatabase(name):
        return User(
                username = name,
                full_name = full_name if full_name else name,
                password = generate_password_hash(passwd),
                email = email if email else name + "@gmail.com",
                )
    return None

def populateUsers():
    users = []
    users.append(createUser("admin", "password"))
    users.append(createUser("user", "123"))
    users.append(createUser("chud", "chud"))

    users.append(createUser("demo", "demo", "demo@pandata.work"))

    for user in users:
        if user is not None:
            db.session.add(user)
            db.session.commit()
