from flask import Blueprint
from app.migrations.users import populateUsers
from app.migrations.projects import populateProjects

CommandsBP = Blueprint('commands', __name__, cli_group=None)

@CommandsBP.cli.command()
def populate():
    populateUsers()
    populateProjects()

