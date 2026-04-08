def test_dashboard_requires_login(client):
    response = client.get("/dashboard/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login?next=/dashboard/" in response.headers["Location"]


def test_dashboard_home_shows_empty_state(client, make_user):
    user = make_user(username="dash_user")

    with client.session_transaction() as session:
        session["user_id"] = user.id

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"No projects yet" in response.data


def test_dashboard_home_lists_project_cards(client, make_user, make_project, add_role):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    project = make_project(owner_id=owner.id, title="Dashboard Project", description="Desc")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    with client.session_transaction() as session:
        session["user_id"] = viewer.id

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"Dashboard Project" in response.data
    assert b"Desc" in response.data
