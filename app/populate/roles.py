from sqlalchemy import select, exists, and_

from app.core import db
from app.tables import Role, Project, User

def checkRoleInDatabase(user_id: str, project_id: str, role: str) -> bool:
    return db.session.execute(
        select(
            exists().where(
                and_(
                    Role.user_id == user_id,
                    Role.project_id == project_id,
                    Role.role == role,
                )
            )
        )
    ).scalar()

def createRole(user_id, project_id, role) -> Role | None:
    if not checkRoleInDatabase(user_id, project_id, role):
        return Role(
                user_id = user_id,
                project_id = project_id,
                role = role,
                )
    return None


def populateRoles():
    users = db.session.execute(select(User)).scalars().all()
    u = {}

    for x in users:
        u[x.username] = x 

    admin = u.get("admin")
    user = u.get("user")
    chud = u.get("chud")
    demo = u.get("demo")

    projects = db.session.execute(select(Project)).scalars().all()
    if not projects:
        return  

    roles: list[Role] = []


    for p in projects:
        if admin:
            r = createRole(admin.id, p.id, "owner")
            if r: 
                roles.append(r)

    half = len(projects) // 2

    if user:
        for p in projects[:half]:
            r = createRole(user.id, p.id, "editor")
            if r: 
                roles.append(r)

    if chud:
        for p in projects[half:]:
            r = createRole(chud.id, p.id, "viewer")
            if r:
                roles.append(r)

    if demo:
        demoProjects = db.session.query(Project).filter_by(owner_id=demo.id).all()

        for p in demoProjects:
            role = createRole(demo.id, p.id, "owner")
            if role is not None:
                roles.append(role)

    if roles:
        db.session.add_all(roles)
        db.session.commit()

