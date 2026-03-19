from flask import Flask, session, render_template, redirect, url_for
from flask_session import Session
import os

from app.config import Config
from app.src.commands import CommandsBP
from app.src.project.queries import get_projects_for_user

from app.routes import DashBP, DebugBP, ProjectBP, DataBP, AuthBP
from app.core import db
import app.tables

def create_app():
    app = Flask(__name__, template_folder='./templates/')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.getenv('FILE_UPLOAD_STORAGE_PATH')
    Session(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error/404.html"), 404

    @app.route('/')
    def mainPage():
        return redirect(url_for("dashboard.get_dashboard_main"))

    app.register_blueprint(AuthBP)
    app.register_blueprint(DashBP, url_prefix='/dashboard/')
    app.register_blueprint(DebugBP, url_prefix='/debug/')
    app.register_blueprint(ProjectBP, url_prefix='/projects/')
    app.register_blueprint(DataBP, url_prefix='/data/')
    app.register_blueprint(CommandsBP)

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.get_dashboard_main'))
        return redirect(url_for('authentication.login'))

    @app.context_processor
    def inject_sidebar_projects():
        user_id = session.get("user_id")

        if not user_id:
            return {"projects": {}}

        return {"projects": get_projects_for_user(user_id)}

    return app
