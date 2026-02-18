from sqlalchemy import select, exists

from app.src.database import db
from app.tables.projects import Project
from app.tables.users import User

def checkProjectInDatabase(title) -> bool:
    return db.session.execute(select(
            exists().where(Project.title == title)
        )).scalar()

def createProject(owner_id, title, desc) -> Project | None:
    if not checkProjectInDatabase(title):
        return Project(
                owner_id = owner_id, 
                title = title,
                description = desc,
                )

def populateProjects():
    adminUser = db.session.query(User).filter_by(username="admin").first()
    userUser = db.session.query(User).filter_by(username="user").first()
    chudUser = db.session.query(User).filter_by(username="chud").first()

    projects = []

    projects.append(createProject(adminUser.id, "Admin Project", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(adminUser.id, "Admin Project 2", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(userUser.id, "Looksmaxing", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(userUser.id, "Meow?", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(chudUser.id, "Chuding101", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))

    for project in projects:
        if project is not None:
            db.session.add(project)
            db.session.commit()
