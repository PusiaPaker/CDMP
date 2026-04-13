from decimal import Decimal, InvalidOperation

from flask import render_template, abort, request, redirect, url_for, flash, session

from app.core import db
from app.tables import Expense, Project
from app.src.utilities import normalize_expense_frequency, parse_import_date
from app.src.project.queries import user_has_project_access, user_can_edit_project

from .project import ProjectBP

from app.src.project.finance import (
    budget_overrun_forecast_data,
    category_cost_split_data,
    compute_total_expenses,
    next_year_spending,
    number_of_recurring_costs,
    running_expense_total_data,
)

@ProjectBP.route("/<project_id>/finance/", methods=["GET", "POST"])
def finance(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if request.method == "POST":
        if not user_can_edit_project(session["user_id"], project_id):
            return render_template("error/unauthorized.html"), 403

        expense_name = request.form.get("expense_name", "").strip()
        expense_purpose = request.form.get("expense_purpose", "").strip() or None
        amount = request.form.get("amount", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        recurrence_type = request.form.get("recurrence_type", "").strip()
        category = request.form.get("category", "").strip() or "unspecified"

        if not all([expense_name, amount, expense_date, recurrence_type]):
            flash("Expense name, amount, date, and frequency are required.", "error")
            return redirect(url_for("project.finance", project_id=project_id, tab="expenses"))

        cleaned_amount = amount.replace(",", "").replace("$", "")

        try:
            normalized_recurrence = normalize_expense_frequency(recurrence_type)
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
            flash("Could not add expense. Check the amount, date, and frequency.", "error")
            return redirect(url_for("project.finance", project_id=project_id, tab="expenses"))

        db.session.add(expense)
        db.session.commit()
        return redirect(url_for("project.finance", project_id=project_id, tab="expenses"))

    active_finance_tab = request.args.get("tab", "analysis")
    if active_finance_tab not in {"analysis", "expenses"}:
        active_finance_tab = "analysis"

    expenses = (
        db.session.query(Expense)
        .filter(Expense.project_id == project_id)
        .order_by(Expense.expense_date.desc())
        .all()
    )

    stats = {
        'total_expenses': compute_total_expenses(expenses),
        'number_recurring_costs': number_of_recurring_costs(expenses),
        'next_year_cost': next_year_spending(expenses),
        'project_budget': project.budget_amount  
    }
    chart_data = running_expense_total_data(expenses)
    budget_forecast_chart_data = budget_overrun_forecast_data(expenses, project.budget_amount)
    category_split_chart_data = category_cost_split_data(expenses)


    return render_template(
        "project/finance.html.j2",
        project=project,
        active_project_id=project.id,
        expenses=expenses,
        active_finance_tab=active_finance_tab,
        finance_stats=stats,
        finance_running_total_data=chart_data,
        finance_budget_forecast_data=budget_forecast_chart_data,
        finance_category_split_data=category_split_chart_data,
        can_edit_project=user_can_edit_project(session["user_id"], project_id),
    ), 200


@ProjectBP.route("/<project_id>/finance/<expense_id>")
def delete_project_expense(project_id, expense_id):
    project = db.session.get(Project, project_id)
    if not project:
        return abort(404)

    if not user_has_project_access(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    if not user_can_edit_project(session["user_id"], project_id):
        return render_template("error/unauthorized.html"), 403

    expense = (
        db.session.query(Expense)
        .filter(Expense.project_id == project_id, Expense.id == expense_id)
        .first()
    )

    if expense:
        db.session.delete(expense)
        db.session.commit()

    return redirect(url_for("project.finance", project_id=project_id, tab="expenses"))
