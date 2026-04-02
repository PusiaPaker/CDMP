def test_project_route_requires_login(client):
    response = client.get("/projects/some-project-id/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login?next=/projects/some-project-id/" in response.headers["Location"]


def test_project_home_returns_404_for_missing_project(client, make_user):
    user = make_user(username="owner")

    with client.session_transaction() as session:
        session["user_id"] = user.id

    response = client.get("/projects/missing-project-id/")

    assert response.status_code == 404


def test_project_home_redirects_without_access(client, make_user, make_project):
    owner = make_user(username="owner")
    outsider = make_user(username="outsider")
    project = make_project(owner_id=owner.id, title="No Access")

    with client.session_transaction() as session:
        session["user_id"] = outsider.id

    response = client.get(f"/projects/{project.id}/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard/")


def test_project_home_returns_200_with_access(
    client,
    make_user,
    make_project,
    add_role,
):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    project = make_project(owner_id=owner.id, title="Accessible")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    with client.session_transaction() as session:
        session["user_id"] = viewer.id

    response = client.get(f"/projects/{project.id}/")

    assert response.status_code == 200
    assert b"Accessible" in response.data
