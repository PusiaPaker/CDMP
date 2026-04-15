from app.core import db
from app.tables import User


class _FakeGoogleOAuthClient:
    def __init__(self):
        self.calls = []

    def authorize_redirect(self, redirect_uri, **kwargs):
        self.calls.append((redirect_uri, kwargs))
        return redirect_uri


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
        data={
            "full_name": "Taken Name",
            "username": "taken",
            "password": "Newpass123!",
            "email": "new@example.com",
        },
    )

    assert response.status_code == 401
    assert b"Username is taken." in response.data


def test_register_rejects_weak_password(client):
    response = client.post(
        "/register",
        data={
            "full_name": "Weak Password User",
            "username": "weak_user",
            "password": "weakpass1",
            "email": "weak@example.com",
        },
    )

    assert response.status_code == 400
    assert b"Password must be 10+ characters" in response.data


def test_register_creates_user_and_redirects(client, app_ctx):
    response = client.post(
        "/register",
        data={
            "full_name": "New User",
            "username": "new_user",
            "password": "Newpass123!",
            "email": "new@example.com",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    created = db.session.query(User).filter_by(username="new_user").first()
    assert created is not None
    assert created.full_name == "New User"
    assert created.email == "new@example.com"


def test_login_google_uses_explicit_google_redirect_uri(client, app, monkeypatch):
    fake_google = _FakeGoogleOAuthClient()
    monkeypatch.setattr("app.routes.auth.oauth.google", fake_google, raising=False)
    app.config.update(
        GOOGLE_OAUTH_ENABLED=True,
        GOOGLE_REDIRECT_URI="https://example.com/login/google/callback",
        APP_BASE_URL="",
    )

    response = client.get("/login/google")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "https://example.com/login/google/callback"
    assert fake_google.calls[0][0] == "https://example.com/login/google/callback"


def test_login_google_builds_redirect_uri_from_app_base_url(client, app, monkeypatch):
    fake_google = _FakeGoogleOAuthClient()
    monkeypatch.setattr("app.routes.auth.oauth.google", fake_google, raising=False)
    app.config.update(
        GOOGLE_OAUTH_ENABLED=True,
        GOOGLE_REDIRECT_URI="",
        APP_BASE_URL="https://cdmp.example.com",
    )

    response = client.get("/login/google")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "https://cdmp.example.com/login/google/callback"
    assert fake_google.calls[0][0] == "https://cdmp.example.com/login/google/callback"
