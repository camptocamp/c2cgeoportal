# pylint: disable=no-self-use

import pytest
from pyramid.view import view_config


@pytest.fixture(scope="class")
@pytest.mark.usefixtures("dbsession")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User

    user = User("babar")
    dbsession.begin_nested()
    dbsession.add(user)
    dbsession.flush()
    yield
    dbsession.rollback()


@view_config(route_name="user_add", renderer="./test_learn.jinja2")
def view_committing_user(request):
    from c2cgeoportal_commons.models.static import User

    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}


@view_config(route_name="users_nb", renderer="./test_learn.jinja2")
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.static import User

    users = request.dbsession.query(User).all()
    username = "None"
    if len(users) > 0:
        username = users[0].username
    return {"size": len(users), "first": username, "project": "c2cgeoportal_admin"}


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:
    @pytest.mark.usefixtures("test_app")
    def test_view_rendering_in_app(self, dbsession, test_app):
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 1', <br/>,"
            " 'first is: babar', <br/>,"
            " 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app(self, dbsession, test_app):
        res = test_app.get("/user_add", status=200)
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 2', <br/>,"
            " 'first is: babar', <br/>,"
            " 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app_rollbacked(self, dbsession, test_app):
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 1', <br/>,"
            " 'first is: babar', <br/>,"
            " 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)
