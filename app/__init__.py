from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from app.routes.dashboard import DashBP
from app.routes.sql_testing import TestBP
from app.routes.auth import AuthBP
from app.config import Config
from app.src.database import db


def create_app():
    app = Flask(__name__, template_folder='./templates/')
    app.config.from_object(Config)
    Session(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(AuthBP)
    app.register_blueprint(DashBP, url_prefix='/dashboard/')
    app.register_blueprint(TestBP, url_prefix='/sql/')

    return app
