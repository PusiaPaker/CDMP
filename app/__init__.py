from flask import Flask, session, redirect, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from app.routes.dashboard import DashBP
from app.routes.sql_testing import DebugBP 
from app.routes.projects import ProjectsBP 
from app.routes.auth import AuthBP
from app.config import Config
from app.src.database import db
from app.src.commands import CommandsBP


def create_app():
    app = Flask(__name__, template_folder='./templates/')
    app.config.from_object(Config)
    Session(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(AuthBP)
    app.register_blueprint(DashBP, url_prefix='/dashboard/')
    app.register_blueprint(DebugBP, url_prefix='/debug/')
    app.register_blueprint(ProjectsBP, url_prefix='/projects/')
    app.register_blueprint(CommandsBP)

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.get_dashboard_main'))
        return redirect(url_for('authentication.login'))

    return app
