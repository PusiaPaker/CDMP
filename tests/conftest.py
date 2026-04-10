import os
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.config import Config
from app.core import db
from app.tables import User, Project, Role


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    session_dir = tmp_path / "flask_session"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setenv("FILE_UPLOAD_STORAGE_PATH", str(upload_dir))
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_file}")
    monkeypatch.setattr(Config, "SESSION_FILE_DIR", str(session_dir), raising=False)

    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with flask_app.app_context():
        db.drop_all()
        db.create_all()

    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield


@pytest.fixture
def make_user(app_ctx):
    def _make_user(username="user", password="password123", email=None, full_name=None):
        if email is None:
            email = f"{username}@example.com"
        if full_name is None:
            full_name = username

        user = User(
            username=username,
            full_name=full_name,
            password=generate_password_hash(password),
            email=email,
        )
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user


@pytest.fixture
def make_project(app_ctx):
    def _make_project(owner_id, title="Project A", description="Test project"):
        project = Project(owner_id=owner_id, title=title, description=description)
        db.session.add(project)
        db.session.commit()
        return project

    return _make_project


@pytest.fixture
def add_role(app_ctx):
    def _add_role(user_id, project_id, role_name="viewer"):
        role = Role(user_id=user_id, project_id=project_id, role=role_name)
        db.session.add(role)
        db.session.commit()
        return role

    return _add_role
