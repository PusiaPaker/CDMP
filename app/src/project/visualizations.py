from sqlalchemy import select
from collections import Counter

from app.core import db
from app.tables import ProjectPerson, TimelineEvent

from dateutil.relativedelta import relativedelta
from datetime import datetime

#
# Functions that will build the data that Chart.js needs to render a chart
#


def build_role_distribution(project_id):
    rows = db.session.execute(
        select(ProjectPerson.role_level).where(ProjectPerson.project_id == project_id)
    ).all()

    roles = []
    for (role_level,) in rows:
        if role_level is None:
            continue

        role_text = str(role_level).strip()
        if not role_text:
            continue

        roles.append(role_text)

    counts = Counter(roles)

    labels = list(counts.keys())
    data = list(counts.values())

    return {
        "labels": labels,
        "data": data,
        "total_roles": len(labels),
        "total_people": sum(data),
    }


def build_event_distribution(project_id):
    events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
            .order_by(TimelineEvent.start_date.asc())
        )
        .scalars().all()
    )

    if not events:
        return {
            "labels": [],
            "data": [],
            "type": "month",
        }

    # if the project event span shorter than a year, display
    # dates monthly, if they are longer than a year, display every quarter
    earliest_date = events[0].start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    latest_date = events[-1].start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    use_quarters = latest_date > (earliest_date + relativedelta(years=1))
    step = relativedelta(months=3 if use_quarters else 1)

    labels = []
    data = []
    current_date = earliest_date
    while current_date <= latest_date:
        next_date = current_date + step

        if use_quarters:
            quarter_num = ((current_date.month - 1) // 3) + 1
            labels.append(f"Q{quarter_num} {current_date.year}")
        else:
            labels.append(current_date.strftime("%b %Y"))

        count = 0
        for event in events:
            if current_date <= event.start_date < next_date:
                count += 1
        data.append(count)

        current_date = next_date

    return {
        "labels": labels,
        "data": data,
        "type": "quarter" if use_quarters else "month",
    }
