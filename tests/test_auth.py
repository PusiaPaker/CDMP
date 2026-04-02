from app.core import db
from app.tables import User


def test_login_get_returns_200(client):
    response = client.get("/login")

    assert response.status_code == 200


def test_login_rejects_invalid_credentials(client):
    response = client.post(
        "/login",
        data={"username": "missing", "password": "wrong"},
    )

    assert response.status_code == 401
    assert b"Bad username or password" in response.data


def test_login_success_sets_session_and_redirects(client, make_user):
    user = make_user(username="alice", password="secret123")

    response = client.post(
        "/login",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard/")

    with client.session_transaction() as session:
        assert session["user_id"] == user.id


def test_register_rejects_duplicate_username(client, make_user):
    make_user(username="taken", password="abc12345")

    response = client.post(
        "/register",
        data={"username": "taken", "password": "newpass123", "email": "new@example.com"},
    )

    assert response.status_code == 401
    assert b"Username is taken." in response.data


def test_register_creates_user_and_redirects(client, app_ctx):
    response = client.post(
        "/register",
        data={"username": "new_user", "password": "newpass123", "email": "new@example.com"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    created = db.session.query(User).filter_by(username="new_user").first()
    assert created is not None
    assert created.email == "new@example.com"
