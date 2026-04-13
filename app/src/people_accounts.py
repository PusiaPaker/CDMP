from sqlalchemy import select

from app.core import db
from app.tables import Person, ProjectPerson, User


def get_user_by_email(email):
    if not email:
        return None

    return db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()


def link_people_for_user(user_id, email):
    if not email:
        return 0

    people = db.session.execute(
        select(Person).where(
            Person.user_id.is_(None),
            Person.email == email,
        )
    ).scalars().all()

    for person in people:
        person.user_id = user_id

    return len(people)


def reconcile_project_people_accounts(project_id):
    matches = db.session.execute(
        select(Person, User.id)
        .join(ProjectPerson, ProjectPerson.person_id == Person.id)
        .join(User, User.email == Person.email)
        .where(
            ProjectPerson.project_id == project_id,
            Person.user_id.is_(None),
        )
    ).all()

    for person, user_id in matches:
        person.user_id = user_id

    return len(matches)
