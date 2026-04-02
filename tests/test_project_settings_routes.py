from app.core import db
from app.tables import Project, Role


def test_project_settings_returns_404_for_missing_project(client, make_user):
    user = make_user(username="owner")

    with client.session_transaction() as session:
        session["user_id"] = user.id

    response = client.get("/projects/missing/settings")

    assert response.status_code == 404


def test_project_settings_redirects_without_access(client, make_user, make_project):
    owner = make_user(username="owner")
    outsider = make_user(username="outsider")
    project = make_project(owner_id=owner.id, title="Private Project")

    with client.session_transaction() as session:
        session["user_id"] = outsider.id

    response = client.get(f"/projects/{project.id}/settings", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard/")


def test_project_settings_returns_200_with_access(client, make_user, make_project, add_role):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    project = make_project(owner_id=owner.id, title="Settings Project")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    with client.session_transaction() as session:
        session["user_id"] = viewer.id

    response = client.get(f"/projects/{project.id}/settings")

    assert response.status_code == 200
    assert b"Settings" in response.data


def test_project_create_get_requires_login(client):
    response = client.get("/projects/new", follow_redirects=False)

    assert response.status_code == 302
    assert "/login?next=/projects/new" in response.headers["Location"]


def test_project_create_post_creates_project_and_owner_role(client, make_user, app_ctx):
    user = make_user(username="creator")

    with client.session_transaction() as session:
        session["user_id"] = user.id

    response = client.post(
        "/projects/new",
        data={"title": "Created Project", "description": "Created from test"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/projects/" in response.headers["Location"]

    created = db.session.query(Project).filter_by(title="Created Project").first()
    assert created is not None

    owner_role = db.session.query(Role).filter_by(project_id=created.id, user_id=user.id).first()
    assert owner_role is not None
    assert owner_role.role == "owner"
