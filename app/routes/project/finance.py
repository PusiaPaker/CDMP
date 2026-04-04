from flask import render_template, abort

from app.core import db
from app.tables import Expense, Project

from .project import ProjectBP

@ProjectBP.route("/<project_id>/finance/", methods=["GET"])
def finance(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    expenses = (
        db.session.query(Expense)
        .filter(Expense.project_id == project_id)
        .order_by(Expense.expense_date.desc())
        .all()
    )

    return render_template(
        "project/finance.html.j2",
        project=project,
        active_project_id=project.id,
        expenses=expenses,
    ), 200
