from flask import Blueprint
from app.populate.users import populateUsers
from app.populate.projects import populateProjects
from app.populate.roles import populateRoles

CommandsBP = Blueprint('commands', __name__, cli_group=None)

@CommandsBP.cli.command()
def populate():
    populateUsers()
    populateProjects()
    populateRoles()

