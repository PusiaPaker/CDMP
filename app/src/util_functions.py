#
# This is just a file for some reusable utility functions we might need
#
from app.src.database import db
from app.tables.projects import Project

def get_all_projects():
    '''
    Retrieve all projects from db
    returns a dictionary where keys are project ids, and each value holds the title and description
    '''

    projects = db.session.query(Project).all()

    result = {}
    for project in projects:
        result[project.id] = {'description': project.description, 'title': project.title}

    return result