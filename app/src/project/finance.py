from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta


def _expense_occurrences(expense, end_date):
    '''
    Return each occurrence date and amount for an expense up to the provided end date.
    Recurring expenses are expanded into monthly or annual occurrences.

    This is used in both the compute_total_expenses and the running_expense_total_data
    utility functions so they match up.
    '''
    occurrences = []

    if not expense.expense_date or expense.expense_date > end_date:
        return occurrences

    amount = expense.amount or Decimal("0")
    recurrence_type = expense.recurrence_type
    start_date = expense.expense_date

    if recurrence_type == 'one_time':
        occurrences.append((start_date, amount))
        return occurrences

    step = 0
    while True:
        if recurrence_type == 'monthly':
            occurrence_date = start_date + relativedelta(months=step)
        elif recurrence_type == 'annual':
            occurrence_date = start_date + relativedelta(years=step)
        else:
            break

        if occurrence_date > end_date:
            break

        occurrences.append((occurrence_date, amount))
        step += 1

    return occurrences


def compute_total_expenses(expenses_list):
    '''
    Computes total expenses up to current day
    '''
    current = datetime.now().date()
    total_amount = Decimal("0")

    for expense in expenses_list:
        for _, amount in _expense_occurrences(expense, current):
            total_amount += amount
    
    return total_amount

def number_of_recurring_costs(expenses_list):
    total = 0

    for expense in expenses_list:
        if expense.recurrence_type != 'one_time':
            total += 1

    return total

def next_year_spending(expenses_list):
    total = Decimal("0")

    for expense in expenses_list:
        if expense.recurrence_type == 'monthly':
            total += (12*expense.amount)
        if expense.recurrence_type == 'annual':
            total += (expense.amount)

    return total


def running_expense_total_data(expenses_list):
    '''
    Compute cumulative project spend over time.
    Recurring expenses are expanded into their monthly or annual occurrences first,
    then same-day charges are grouped before building the running sum.

    NOTE: right now this util will make it so labels are EVERY occurence of expenses,
    Since recurring expenses can only be monthly/annual then it looks mostly ok (x-axis
    labels look like they are month to motnh). But if we test it with a lot one-time expenses
    at different dates it may look cluttered.
    '''
    current = datetime.now().date()
    totals_by_date = defaultdict(lambda: Decimal("0"))

    for expense in expenses_list:
        for occurrence_date, amount in _expense_occurrences(expense, current):
            totals_by_date[occurrence_date] += amount

    running_total = Decimal("0")
    labels = []
    data = []

    for expense_date in sorted(totals_by_date):
        running_total += totals_by_date[expense_date]
        labels.append(expense_date.isoformat())
        data.append(round(float(running_total), 2))

    return {
        "labels": labels,
        "data": data,
    }
