from datetime import datetime

from sqlalchemy import select, exists, and_

from app.core import db
from app.tables import Role, Project, User, TimelineEvent

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

    now = datetime.now()
    result = {}
    for project in projects:
        upcoming_event = (
            db.session.execute(
                select(TimelineEvent)
                .where(
                    TimelineEvent.project_id == project.id,
                    TimelineEvent.start_date >= now,
                )
                .order_by(TimelineEvent.start_date.asc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        result[project.id] = {
            "description": project.description,
            "title": project.title,
            "budget_amount": f"${project.budget_amount:,.2f}" if project.budget_amount is not None else "Not set",
            "upcoming_event_title": upcoming_event.title if upcoming_event else "No upcoming events",
            "upcoming_event_date": upcoming_event.start_date.strftime("%b %d, %Y") if upcoming_event else "",
        }

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
