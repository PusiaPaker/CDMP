from decimal import Decimal, InvalidOperation
from sqlalchemy import select, exists, and_, insert

from app.core import db
from app.tables import Expense, Project, ProjectPerson, Person, TimelineEvent
from app.src.utilities import normalize_expense_frequency, parse_import_date

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

All handlers return:
- A dictionary of shape: {'created': X, 'skipped': Y}
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

    return {
        'created': created_people,
        'skipped': skipped 
    }


def events_mapping_handler(project_id, rows, mapped_to_index):
    title_i = mapped_to_index["Title"]
    start_date_i = mapped_to_index["Start Date"]
    end_date_i = mapped_to_index["End Date"]
    description_i = mapped_to_index["Description"]

    created = 0
    skipped = 0

    for row in rows:
        title = _get(row, title_i)
        start_date = _get(row, start_date_i)
        end_date = _get(row, end_date_i)
        description = _get(row, description_i)

        if (not start_date) and (not end_date):
            skipped += 1
            continue
        
        if not title:
            skipped += 1
            continue

        # some events are "single date" (i.e don't have start and end dates)
        # add flexibility for either end/start date to be the "single date"
        single_date = None
        try:
            if (start_date is None) ^ (end_date is None):
                single_date = end_date if start_date is None else start_date
                single_date = parse_import_date(single_date, as_datetime=True)

            if not single_date:
                start_date = parse_import_date(start_date, as_datetime=True)
                end_date = parse_import_date(end_date, as_datetime=True)
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
        except ValueError:
            skipped += 1
            continue

        db.session.add(timeline_event)
        db.session.commit()
        created += 1
    
    return {
        'created': created,
        'skipped': skipped
    }


def expenses_mapping_handler(project_id, rows, mapped_to_index):
    expense_name_i = mapped_to_index["Expense Name"]
    expense_purpose_i = mapped_to_index["Expense Purpose"]
    amount_i = mapped_to_index["Amount"]
    expense_date_i = mapped_to_index["Date"]
    recurrence_type_i = mapped_to_index["Frequency"]
    category_i = mapped_to_index["Category"]

    created = 0
    skipped = 0

    for row in rows:
        expense_name = _get(row, expense_name_i)
        expense_purpose = _get(row, expense_purpose_i) or ""
        amount = _get(row, amount_i)
        expense_date = _get(row, expense_date_i)
        recurrence_type = _get(row, recurrence_type_i)
        category = _get(row, category_i) or "unspecified"

        if not all([expense_name, amount, expense_date, recurrence_type]):
            skipped += 1
            continue

        try:
            normalized_recurrence = normalize_expense_frequency(recurrence_type)
        except ValueError:
            skipped += 1
            continue

        cleaned_amount = amount.replace(",", "").replace("$", "")

        try:
            expense = Expense(
                project_id=project_id,
                expense_name=expense_name,
                expense_purpose=expense_purpose,
                amount=Decimal(cleaned_amount),
                expense_date=parse_import_date(expense_date),
                recurrence_type=normalized_recurrence,
                category=category,
            )
        except (ValueError, InvalidOperation):
            skipped += 1
            continue

        db.session.add(expense)
        created += 1

    db.session.commit()

    return {
        'created': created,
        'skipped': skipped
    }
