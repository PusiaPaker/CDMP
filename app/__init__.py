from flask import Flask
from app.routes.dashboard import DashBP

def create_app():
    app = Flask(__name__)

    app.register_blueprint(DashBP)

    return app
