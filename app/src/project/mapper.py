from sqlalchemy import select, exists, and_, insert
from app.core import db
from app.tables import Project, ProjectPerson, Person, TimelineEvent
from datetime import datetime

#
# Functions for handling column mapping related functionality
#

# Utilities
def _get(row: list[str], idx: int | None):
    if idx is None:
        return None
    if idx >= len(row):
        return None
    v = row[idx]
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None

# Handlers for mapping to different tables
'''
All handlers take parameters:
- project_id:
- rows: from read_all_csv_rows/read_all_xlsx_rows
- mapped_to_index: a collections.defaultdict that maps each expected column value
        to the index in the "rows", the defaultdict should be created with
        "lambda: None" as the default value.
'''
def people_mapping_handler(project_id, rows, mapped_to_index):
    name_i = mapped_to_index["Name"]
    email_i = mapped_to_index["Email"]
    phone_i = mapped_to_index["Phone"]
    title_i = mapped_to_index["Job Title"]
    role_level_i = mapped_to_index["Role"]

    created_people = 0
    assigned = 0
    skipped = 0

    for row in rows:
        name = _get(row, name_i)
        email = _get(row, email_i)
        phone = _get(row, phone_i)
        title = _get(row, title_i)
        role_level = _get(row, role_level_i)

        if email:
            email = email.strip().lower()

        if not name and not email:
            skipped += 1
            continue

        if not name:
            name = "Unknown"

        person = None

        if email:
            person = db.session.execute(
                select(Person).where(Person.email == email)
            ).scalar_one_or_none()

            if not person:
                person = Person(name=name, email=email, phone=phone, title=title)
                db.session.add(person)
                db.session.flush()
                created_people += 1
        else:
            person = Person(name=name, email=None, phone=phone, title=title)
            db.session.add(person)
            db.session.flush()
            created_people += 1

        already_assigned = db.session.execute(
            select(
                exists().where(
                    and_(
                        ProjectPerson.project_id == project_id,
                        ProjectPerson.person_id == person.id,
                    )
                )
            )
        ).scalar()

        if not already_assigned:
            db.session.add(ProjectPerson(project_id=project_id, person_id=person.id, role_level=role_level))
            assigned += 1

    db.session.commit()


def events_mapping_handler(project_id, rows, mapped_to_index):
    title_i = mapped_to_index["Title"]
    start_date_i = mapped_to_index["Start Date"]
    end_date_i = mapped_to_index["End Date"]
    description_i = mapped_to_index["Description"]

    for row in rows:
        title = _get(row, title_i)
        start_date = _get(row, start_date_i)
        end_date = _get(row, end_date_i)
        description = _get(row, description_i)

        if (not start_date) and (not end_date):
            continue
        
        if not title:
            continue

        # some events are "single date" (i.e don't have start and end dates)
        # add flexibility for either end/start date to be the "single date"
        single_date = None
        if (start_date is None) ^ (end_date is None):
            single_date = end_date if start_date is None else start_date
            single_date = datetime.strptime(single_date, "%Y-%m-%d")

        if not single_date:
            start_date, end_date = datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d")
            timeline_event = TimelineEvent(project_id=project_id,
                                        title=title,
                                        description=description,
                                        start_date=start_date,
                                        end_date=end_date)
        else:
            timeline_event = TimelineEvent(project_id=project_id,
                                        title=title,
                                        description=description,
                                        start_date=single_date,
                                        end_date=None)

        db.session.add(timeline_event)
        db.session.commit()