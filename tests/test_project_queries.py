from app.src.project.queries import (
    user_has_project_access,
    user_is_project_owner,
    get_projects_for_user,
)


def test_user_has_project_access_true_false(make_user, make_project, add_role):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    outsider = make_user(username="outsider")
    project = make_project(owner_id=owner.id, title="Access Test")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    assert user_has_project_access(viewer.id, project.id) is True
    assert user_has_project_access(outsider.id, project.id) is False


def test_user_is_project_owner_true_false(make_user, make_project, add_role):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    project = make_project(owner_id=owner.id, title="Owner Test")
    add_role(user_id=owner.id, project_id=project.id, role_name="owner")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    assert user_is_project_owner(owner.id, project.id) is True
    assert user_is_project_owner(viewer.id, project.id) is False


def test_get_projects_for_user_returns_expected_shape(make_user, make_project, add_role):
    owner = make_user(username="owner")
    viewer = make_user(username="viewer")
    project = make_project(owner_id=owner.id, title="Shape Test", description="Desc")
    add_role(user_id=viewer.id, project_id=project.id, role_name="viewer")

    result = get_projects_for_user(viewer.id)

    assert project.id in result
    assert result[project.id]["title"] == "Shape Test"
    assert result[project.id]["description"] == "Desc"
