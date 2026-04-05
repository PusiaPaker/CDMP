from flask import render_template, abort

from app.core import db
from app.tables import Expense, Project

from .project import ProjectBP

from app.src.project.finance import (
    compute_total_expenses,
    next_year_spending,
    number_of_recurring_costs,
    running_expense_total_data,
)

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

    stats = {
        'total_expenses': compute_total_expenses(expenses),
        'number_recurring_costs': number_of_recurring_costs(expenses),
        'next_year_cost': next_year_spending(expenses)
    }
    chart_data = running_expense_total_data(expenses)

    print(chart_data)

    return render_template(
        "project/finance.html.j2",
        project=project,
        active_project_id=project.id,
        expenses=expenses,
        finance_stats=stats,
        finance_running_total_data=chart_data,
    ), 200
