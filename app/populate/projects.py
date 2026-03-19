from sqlalchemy import select, exists

from app.core import db
from app.tables import Project, User

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
    demoUser = db.session.query(User).filter_by(username="demo").first()

    projects = []

    projects.append(createProject(adminUser.id, "Admin Project", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(adminUser.id, "Admin Project 2", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(userUser.id, "Looksmaxing", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(userUser.id, "Meow?", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))
    projects.append(createProject(chudUser.id, "Chuding101", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum, est sit amet sollicitudin mattis, ex neque volutpat arcu, vestibulum."))

    projects.append(createProject(
        demoUser.id,
        "Northwind CRM Modernization",
        "Modernizing customer account workflows, lead handoff, and support visibility across sales operations."
    ))
    projects.append(createProject(
        demoUser.id,
        "Harbor Health Referral Operations",
        "Improving referral intake, routing, and follow-up workflows for a regional healthcare organization."
    ))
    projects.append(createProject(
        demoUser.id,
        "Meridian Claims Automation",
        "Reducing manual claims handling through triage automation, dashboarding, and exception review."
    ))
    projects.append(createProject(
        demoUser.id,
        "Atlas Vendor Risk Portal",
        "Building a centralized vendor onboarding and risk review portal for procurement and compliance teams."
    ))
    projects.append(createProject(
        demoUser.id,
        "Bluepeak Workforce Planning",
        "Launching staffing, capacity, and forecasting workflows for workforce planning leadership."
    ))

    for project in projects:
        if project is not None:
            db.session.add(project)
            db.session.commit()
