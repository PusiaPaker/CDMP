from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

RECURRING_EXPENSE_TYPES = {"monthly", "annual"}


def _next_occurrence_date(current_date, recurrence_type):
    if recurrence_type == "monthly":
        return current_date + relativedelta(months=1)

    if recurrence_type == "annual":
        return current_date + relativedelta(years=1)

    return None


def _expense_occurrences(expense, end_date):
    if not expense.expense_date or expense.expense_date > end_date:
        return []

    occurrences = []
    amount = expense.amount or Decimal("0")
    occurrence_date = expense.expense_date

    while occurrence_date and occurrence_date <= end_date:
        occurrences.append((occurrence_date, amount))
        occurrence_date = _next_occurrence_date(occurrence_date, expense.recurrence_type)

    return occurrences


def _month_start(date_value):
    return date_value.replace(day=1)


def _month_end(date_value):
    return _month_start(date_value) + relativedelta(months=1, days=-1)


def _month_label(date_value):
    return date_value.strftime("%b %Y")


def _occurrence_totals_by_date(expenses_list, end_date):
    totals_by_date = defaultdict(lambda: Decimal("0"))

    for expense in expenses_list:
        for occurrence_date, amount in _expense_occurrences(expense, end_date):
            totals_by_date[occurrence_date] += amount

    return totals_by_date


def _running_total_series(totals_by_date):
    running_total = Decimal("0")
    labels = []
    data = []

    for expense_date in sorted(totals_by_date):
        running_total += totals_by_date[expense_date]
        labels.append(expense_date.isoformat())
        data.append(round(float(running_total), 2))

    return labels, data


def _empty_budget_forecast_payload():
    return {
        "labels": [],
        "actual_data": [],
        "forecast_data": [],
        "budget_data": [],
        "crosses_budget_on": None,
        "already_over_budget": False,
    }


def _future_recurring_occurrences(expenses_list, start_date, max_months=60):
    occurrences = []
    horizon_date = _month_end(_month_start(start_date) + relativedelta(months=max_months - 1))

    for expense in expenses_list:
        if expense.recurrence_type not in RECURRING_EXPENSE_TYPES:
            continue

        if not expense.expense_date:
            continue

        amount = expense.amount or Decimal("0")
        occurrence_date = expense.expense_date

        while occurrence_date and occurrence_date <= start_date:
            occurrence_date = _next_occurrence_date(occurrence_date, expense.recurrence_type)

        while occurrence_date and occurrence_date <= horizon_date:
            occurrences.append((occurrence_date, amount))
            occurrence_date = _next_occurrence_date(occurrence_date, expense.recurrence_type)

    occurrences.sort(key=lambda occurrence: occurrence[0])
    return occurrences


def _occurrence_totals_by_month(occurrences):
    totals_by_month = defaultdict(lambda: Decimal("0"))

    for occurrence_date, amount in occurrences:
        totals_by_month[_month_start(occurrence_date)] += amount

    return totals_by_month


def _base_forecast_chart(expenses_list, current_date, current_total, budget_amount):
    labels, actual_data = _running_total_series(
        _occurrence_totals_by_date(expenses_list, current_date)
    )

    current_label = current_date.isoformat()
    current_total_float = round(float(current_total), 2)
    budget_float = round(float(budget_amount), 2)

    if not labels or labels[-1] != current_label:
        labels.append(current_label)
        actual_data.append(current_total_float)

    forecast_data = [None] * len(labels)
    forecast_data[-1] = current_total_float

    return {
        "labels": labels,
        "actual_data": actual_data,
        "forecast_data": forecast_data,
        "budget_data": [budget_float] * len(labels),
    }


def compute_total_expenses(expenses_list):
    current = datetime.now().date()
    totals_by_date = _occurrence_totals_by_date(expenses_list, current)
    return sum(totals_by_date.values(), Decimal("0"))


def number_of_recurring_costs(expenses_list):
    total = 0

    for expense in expenses_list:
        if expense.recurrence_type in RECURRING_EXPENSE_TYPES:
            total += 1

    return total


def next_year_spending(expenses_list):
    total = Decimal("0")

    for expense in expenses_list:
        amount = expense.amount or Decimal("0")

        if expense.recurrence_type == 'monthly':
            total += 12 * amount
        if expense.recurrence_type == 'annual':
            total += amount

    return total


def running_expense_total_data(expenses_list):
    current = datetime.now().date()
    labels, data = _running_total_series(_occurrence_totals_by_date(expenses_list, current))

    return {
        "labels": labels,
        "data": data,
    }


def budget_overrun_forecast_data(expenses_list, project_budget, max_months=60):
    if project_budget is None:
        return _empty_budget_forecast_payload()

    current = datetime.now().date()
    budget_amount = Decimal(project_budget)
    current_total = compute_total_expenses(expenses_list)
    chart_data = _base_forecast_chart(
        expenses_list,
        current,
        current_total,
        budget_amount,
    )

    if current_total >= budget_amount:
        chart_data["crosses_budget_on"] = current.isoformat()
        chart_data["already_over_budget"] = True
        return chart_data

    future_occurrences = _future_recurring_occurrences(
        expenses_list,
        current,
        max_months=max_months,
    )
    if not future_occurrences:
        return _empty_budget_forecast_payload()

    projected_total = current_total
    crosses_budget_on = None
    capped_occurrences = []

    for occurrence_date, amount in future_occurrences:
        projected_total += amount
        capped_occurrences.append((occurrence_date, amount))

        if projected_total >= budget_amount:
            crosses_budget_on = occurrence_date
            break

    monthly_totals = _occurrence_totals_by_month(capped_occurrences)

    if crosses_budget_on:
        end_month = _month_start(crosses_budget_on)
    else:
        end_month = _month_start(current) + relativedelta(months=max_months - 1)

    month_cursor = _month_start(current)
    if monthly_totals[month_cursor] == 0:
        month_cursor += relativedelta(months=1)

    projected_total = current_total
    while month_cursor <= end_month:
        projected_total += monthly_totals[month_cursor]
        chart_data["labels"].append(_month_label(month_cursor))
        chart_data["actual_data"].append(None)
        chart_data["forecast_data"].append(round(float(projected_total), 2))
        chart_data["budget_data"].append(chart_data["budget_data"][0])
        month_cursor += relativedelta(months=1)

    chart_data["crosses_budget_on"] = (
        crosses_budget_on.isoformat() if crosses_budget_on else None
    )
    chart_data["already_over_budget"] = False
    return chart_data
