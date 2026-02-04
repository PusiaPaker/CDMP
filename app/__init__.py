from flask import Flask
from app.routes.dashboard import DashBP
from app.routes.sql_testing import TestBP

def create_app():
    app = Flask(__name__)

    app.register_blueprint(DashBP)
    app.register_blueprint(TestBP, url_prefix='/sql/')

    return app
