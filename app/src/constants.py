#
# File for us to store some global constants
#

ALLOWED_FILE_EXTENSIONS = ['docx', 'pdf', 'csv', 'xlsx', 'xls', 'png']
ALLOWED_FILE_CATEGORIES = ['unspecified', 'text', 'image', 'spreadsheet']

# column mapper column data (per "table type")
table_type_columns = {
    'people': {
        'required': ['Name', 'Job Title', 'Role'],
        'optional': ['Email', 'Phone']
    },
    'timeline': {
        'required': ['Start Date', 'Title',],
        'optional': ['End Date', 'Description']
    },
    'expenses': {
        'required': ['Expense Name', 'Amount', 'Date', 'Frequency'],
        'optional': ['Expense Purpose', 'Category']
    }
}
