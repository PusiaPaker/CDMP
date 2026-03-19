from flask import Blueprint
from app.populate.users import populateUsers
from app.populate.projects import populateProjects
from app.populate.roles import populateRoles
from app.populate.people import populatePeople

CommandsBP = Blueprint('commands', __name__, cli_group=None)

@CommandsBP.cli.command()
def populate():
    populateUsers()
    populateProjects()
    populateRoles()
    populatePeople()

