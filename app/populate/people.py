from sqlalchemy import select, exists, and_

from app.core import db
from app.tables import Project, Person, ProjectPerson, PersonReport


def checkPersonInDatabase(email) -> bool:
    return db.session.execute(
        select(exists().where(Person.email == email))
    ).scalar()


def createPerson(name, email, phone, title) -> Person | None:
    if not checkPersonInDatabase(email):
        return Person(
            name=name,
            email=email,
            phone=phone,
            title=title,
        )
    return None


def checkProjectPersonInDatabase(project_id, person_id) -> bool:
    return db.session.execute(
        select(
            exists().where(
                and_(
                    ProjectPerson.project_id == project_id,
                    ProjectPerson.person_id == person_id,
                )
            )
        )
    ).scalar()


def createProjectPerson(project_id, person_id, role_level) -> ProjectPerson | None:
    if not checkProjectPersonInDatabase(project_id, person_id):
        return ProjectPerson(
            project_id=project_id,
            person_id=person_id,
            role_level=role_level,
        )
    return None


def checkPersonReportInDatabase(person_id, reports_to_id) -> bool:
    return db.session.execute(
        select(
            exists().where(
                and_(
                    PersonReport.person_id == person_id,
                    PersonReport.reports_to_id == reports_to_id,
                )
            )
        )
    ).scalar()


def createPersonReport(person_id, reports_to_id) -> PersonReport | None:
    if person_id == reports_to_id:
        return None

    if not checkPersonReportInDatabase(person_id, reports_to_id):
        return PersonReport(
            person_id=person_id,
            reports_to_id=reports_to_id,
        )
    return None


def getPersonByEmail(email) -> Person | None:
    return db.session.query(Person).filter_by(email=email).first()


def populatePeople():
    project_people_map = {
        "Northwind CRM Modernization": {
            "people": [
                ("Ava Patel", "ava.patel@northwind-demo.com", "555-210-1001", "Director of Revenue Systems", "Director"),
                ("Noah Kim", "noah.kim@northwind-demo.com", "555-210-1002", "Engineering Manager", "Engineering Manager"),
                ("Sofia Martinez", "sofia.martinez@northwind-demo.com", "555-210-1003", "Senior Backend Engineer", "Backend Engineer"),
                ("Ethan Brooks", "ethan.brooks@northwind-demo.com", "555-210-1004", "Frontend Engineer", "Frontend Engineer"),
                ("Mia Chen", "mia.chen@northwind-demo.com", "555-210-1005", "Sales Operations Analyst", "Analyst"),
                ("Liam Carter", "liam.carter@northwind-demo.com", "555-210-1006", "QA Lead", "QA Lead"),
            ],
            "reports": [
                ("Noah Kim", "Ava Patel"),
                ("Sofia Martinez", "Noah Kim"),
                ("Ethan Brooks", "Noah Kim"),
                ("Mia Chen", "Ava Patel"),
                ("Liam Carter", "Noah Kim"),
            ],
        },
        "Harbor Health Referral Operations": {
            "people": [
                ("Grace Holloway", "grace.holloway@harbor-demo.com", "555-220-1001", "Operations Director", "Director"),
                ("Oliver Grant", "oliver.grant@harbor-demo.com", "555-220-1002", "Implementation Lead", "Implementation Lead"),
                ("Chloe Nguyen", "chloe.nguyen@harbor-demo.com", "555-220-1003", "Business Analyst", "Business Analyst"),
                ("James Foster", "james.foster@harbor-demo.com", "555-220-1004", "Data Engineer", "Data Engineer"),
                ("Ella Ramirez", "ella.ramirez@harbor-demo.com", "555-220-1005", "Training Specialist", "Training Specialist"),
            ],
            "reports": [
                ("Oliver Grant", "Grace Holloway"),
                ("Chloe Nguyen", "Oliver Grant"),
                ("James Foster", "Oliver Grant"),
                ("Ella Ramirez", "Oliver Grant"),
            ],
        },
        "Meridian Claims Automation": {
            "people": [
                ("Benjamin Ross", "benjamin.ross@meridian-demo.com", "555-230-1001", "VP of Claims Transformation", "VP"),
                ("Harper Lee", "harper.lee@meridian-demo.com", "555-230-1002", "Product Manager", "Product Manager"),
                ("Lucas White", "lucas.white@meridian-demo.com", "555-230-1003", "Automation Engineer", "Automation Engineer"),
                ("Amelia Scott", "amelia.scott@meridian-demo.com", "555-230-1004", "Rules Analyst", "Analyst"),
                ("Henry Turner", "henry.turner@meridian-demo.com", "555-230-1005", "QA Analyst", "QA Analyst"),
                ("Zoe Adams", "zoe.adams@meridian-demo.com", "555-230-1006", "Operations Supervisor", "Operations Supervisor"),
            ],
            "reports": [
                ("Harper Lee", "Benjamin Ross"),
                ("Lucas White", "Harper Lee"),
                ("Amelia Scott", "Harper Lee"),
                ("Henry Turner", "Harper Lee"),
                ("Zoe Adams", "Benjamin Ross"),
            ],
        },
        "Atlas Vendor Risk Portal": {
            "people": [
                ("Isabella Ward", "isabella.ward@atlas-demo.com", "555-240-1001", "Security Director", "Director"),
                ("Daniel Evans", "daniel.evans@atlas-demo.com", "555-240-1002", "Compliance Manager", "Compliance Manager"),
                ("Scarlett Baker", "scarlett.baker@atlas-demo.com", "555-240-1003", "UX Designer", "UX Designer"),
                ("Logan Price", "logan.price@atlas-demo.com", "555-240-1004", "Full Stack Engineer", "Full Stack Engineer"),
                ("Victoria Morris", "victoria.morris@atlas-demo.com", "555-240-1005", "Risk Analyst", "Risk Analyst"),
            ],
            "reports": [
                ("Daniel Evans", "Isabella Ward"),
                ("Scarlett Baker", "Daniel Evans"),
                ("Logan Price", "Daniel Evans"),
                ("Victoria Morris", "Daniel Evans"),
            ],
        },
        "Bluepeak Workforce Planning": {
            "people": [
                ("Nathan Cooper", "nathan.cooper@bluepeak-demo.com", "555-250-1001", "Operations Executive", "Executive Sponsor"),
                ("Lily Sanders", "lily.sanders@bluepeak-demo.com", "555-250-1002", "Workforce Planning Manager", "Planning Manager"),
                ("Gabriel Perry", "gabriel.perry@bluepeak-demo.com", "555-250-1003", "Reporting Engineer", "Reporting Engineer"),
                ("Hannah Flores", "hannah.flores@bluepeak-demo.com", "555-250-1004", "Staffing Analyst", "Analyst"),
                ("Jack Bell", "jack.bell@bluepeak-demo.com", "555-250-1005", "Forecasting Analyst", "Analyst"),
                ("Aria Murphy", "aria.murphy@bluepeak-demo.com", "555-250-1006", "Change Manager", "Change Manager"),
            ],
            "reports": [
                ("Lily Sanders", "Nathan Cooper"),
                ("Gabriel Perry", "Lily Sanders"),
                ("Hannah Flores", "Lily Sanders"),
                ("Jack Bell", "Lily Sanders"),
                ("Aria Murphy", "Nathan Cooper"),
            ],
        },
    }

    for project_title, data in project_people_map.items():
        project = db.session.query(Project).filter_by(title=project_title).first()
        if not project:
            continue

        peopleByName = {}

        for name, email, phone, title, role_level in data["people"]:
            person = createPerson(name, email, phone, title)

            if person is not None:
                db.session.add(person)
                db.session.commit()
                peopleByName[name] = person
            else:
                peopleByName[name] = getPersonByEmail(email)

            projectPerson = createProjectPerson(
                project.id,
                peopleByName[name].id,
                role_level,
            )

            if projectPerson is not None:
                db.session.add(projectPerson)
                db.session.commit()

        for person_name, manager_name in data["reports"]:
            person = peopleByName.get(person_name)
            manager = peopleByName.get(manager_name)

            if person is None or manager is None:
                continue

            report = createPersonReport(person.id, manager.id)
            if report is not None:
                db.session.add(report)
                db.session.commit()
