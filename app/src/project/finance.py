from datetime import datetime
from dateutil.relativedelta import relativedelta

def compute_total_expenses(expenses_list):
    '''
    Computes total expenses up to current day
    '''
    current = datetime.now()
    total_amount = 0

    for expense in expenses_list:
        if expense.recurrence_type == 'one_time':
            total_amount += expense.amount

        # for these next two I did +1 so that if we are in same month
        # or year it counts a "first charge" or whatever (it works)
        elif expense.recurrence_type == 'monthly':
            delta = relativedelta(current, expense.expense_date)
            months = (delta.years * 12 + delta.months) + 1

            print(f'{months} months * {expense.amount}')
            total_amount += (months * expense.amount)
        elif expense.recurrence_type == 'annual':
            delta = relativedelta(current, expense.expense_date)
            years = delta.years + 1

            print(f'{years} years * {expense.amount}')
            total_amount += (years * expense.amount)
    
    return total_amount

def number_of_recurring_costs(expenses_list):
    total = 0

    for expense in expenses_list:
        if expense.recurrence_type != 'one_time':
            total += 1

    return total

def next_year_spending(expenses_list):
    total = 0

    for expense in expenses_list:
        if expense.recurrence_type == 'monthly':
            total += (12*expense.amount)
        if expense.recurrence_type == 'annual':
            total += (expense.amount)

    return total