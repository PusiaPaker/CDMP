from flask import Flask, session, render_template, redirect, url_for
from flask_session import Session
import os
from sqlalchemy import inspect, text

from app.config import Config
from app.src.commands import CommandsBP
from app.src.project.queries import get_projects_for_user

from app.routes import DashBP, DebugBP, ProjectBP, DataBP, AuthBP
from app.core import db, oauth
import app.tables


def _upgrade_existing_schema():
    inspector = inspect(db.engine)

    if "projects" not in inspector.get_table_names():
        return

    project_columns = {column["name"] for column in inspector.get_columns("projects")}
    if "budget_amount" not in project_columns:
        db.session.execute(text("ALTER TABLE projects ADD COLUMN budget_amount NUMERIC(12, 2)"))
        db.session.commit()

def create_app():
    app = Flask(__name__, template_folder='./templates/')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.getenv('FILE_UPLOAD_STORAGE_PATH')

    if app.config.get("GOOGLE_OAUTH_ENABLED") and app.config.get("SECRET_KEY") == "dev-insecure-change-me":
        raise RuntimeError("Set a strong SECRET_KEY before enabling Google Sign-In.")

    Session(app)
    oauth.init_app(app)

    #Google Oauth info below
    #Can be changed in .env file i think

    if app.config.get("GOOGLE_OAUTH_ENABLED"):
        oauth.register(
            "google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
            client_kwargs={"scope": "openid email profile https://www.googleapis.com/auth/calendar.readonly"},
        )

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _upgrade_existing_schema()

    # Not every route passes projects for us, so this just makes sure that it doesn't break randomly
    @app.context_processor
    def inject_sidebar_projects():
        if "user_id" not in session:
            return {"sidebar_projects": {}}
        return { "sidebar_projects": get_projects_for_user(session["user_id"])}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error/404.html"), 404

    @app.route('/')
    def mainPage():
        if "user_id" in session:
            return redirect(url_for("dashboard.main"))
        return render_template("auth/landing.html")

    app.register_blueprint(AuthBP)
    app.register_blueprint(DashBP, url_prefix='/dashboard/')
    app.register_blueprint(DebugBP, url_prefix='/debug/')
    app.register_blueprint(ProjectBP, url_prefix='/projects/')
    app.register_blueprint(DataBP, url_prefix='/data/')
    app.register_blueprint(CommandsBP)

    return app
