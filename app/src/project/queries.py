from sqlalchemy import select, exists, and_

from app.core import db
from app.tables import Role, Project, User, Person, ProjectPerson, File

def user_has_project_access(user_id: str, project_id: str) -> bool:
    return db.session.execute(
        select(
            exists().where(
                and_(
                    Role.user_id == user_id,
                    Role.project_id == project_id,
                )
            )
        )
    ).scalar()

def user_is_project_owner(user_id: str, project_id: str) -> bool:
    return db.session.execute(
        select(
            exists().where(
                and_(
                    Role.user_id == user_id,
                    Role.project_id == project_id,
                    Role.role == "owner"
                )
            )
        )
    ).scalar()

def get_projects_for_user(user_id: str) -> dict[str, dict[str, str]]:
    projects = (
        db.session.execute(
            select(Project)
            .join(Role, Role.project_id == Project.id)
            .where(Role.user_id == user_id)
            .distinct()
        )
        .scalars()
        .all()
    )

    result = {}
    for project in projects:
        result[project.id] = {"description": project.description, "title": project.title}

    return result

def get_users_from_project(project_id: str) -> list[str, dict[str]]:
    roles = (
        db.session.execute(
            select(Role)
            .where(Role.project_id == project_id)
        )
        .scalars()
        .all()
    )
    users = []
    for role in roles:
        users.append([db.session.execute(
            select(User)
            .where(User.id == role.user_id)
        ).scalars().first(), role.role])
    return users

def get_all_projects():
    '''
    Retrieve all projects from db
    returns a dictionary where keys are project ids, and each value holds the title and description
    '''

    projects = db.session.query(Project).all()

    result = {}
    for project in projects:
        result[project.id] = {'description': project.description, 'title': project.title}

    return result


def get_project_people_rows(project_id: str):
    return (
        db.session.execute(
            select(Person, ProjectPerson)
            .join(ProjectPerson, ProjectPerson.person_id == Person.id)
            .where(ProjectPerson.project_id == project_id)
            .order_by(Person.name.asc())
        )
        .all()
    )


def get_project_recent_files(project_id: str, limit: int = 6):
    return (
        db.session.execute(
            select(File)
            .where(File.project_id == project_id)
            .order_by(File.upload_date.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def get_project_workspace_context(project_id: str) -> dict:
    return {
        "people_rows": get_project_people_rows(project_id),
        "recent_files": get_project_recent_files(project_id),
    }

