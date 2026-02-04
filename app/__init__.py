from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from app.routes.dashboard import DashBP
from app.routes.sql_testing import TestBP
from app.config import Config
from app.src.database import db


def create_app():
    app = Flask(__name__, template_folder='./templates/')
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(DashBP)
    app.register_blueprint(TestBP, url_prefix='/sql/')

    return app
