# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture
def left_menu_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Role

    roles = []
    role = Role("secretary")
    dbsession.add(role)
    roles.append(role)

    dbsession.flush()

    return {"roles": roles}


@pytest.mark.usefixtures("test_app")
class TestLeftMenu(AbstractViewsTests):
    _prefix = "/admin/roles"

    def test_index(self, test_app) -> None:
        resp = test_app.get("/admin/roles", status=200)
        self.check_left_menu(resp, "Roles")

    @pytest.mark.usefixtures("left_menu_test_data")
    def test_edit(self, test_app, left_menu_test_data) -> None:
        role = left_menu_test_data["roles"][0]
        resp = self.get_item(test_app, role.id)
        self.check_left_menu(resp, "Roles")
