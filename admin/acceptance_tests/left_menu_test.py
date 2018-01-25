# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def left_menu_test_data(dbsession):
    from c2cgeoportal_commons.models.main import Role

    dbsession.begin_nested()

    roles = []
    role = Role('secretary')
    dbsession.add(role)
    roles.append(role)
    dbsession.flush()

    yield {
        'roles': roles
    }

    dbsession.rollback()


@pytest.mark.usefixtures('test_app')
class TestLeftMenu(AbstractViewsTests):

    _prefix = '/roles'

    def test_404(self, test_app):
        resp = test_app.get('/this/is/notfound/', status=404)
        assert resp.html.select_one('.navbar') is not None
        assert resp.html.select_one('.navbar li.active a') is None

    def test_index(self, test_app):
        resp = test_app.get('/roles', status=200)
        self.check_left_menu(resp, 'Roles')

    @pytest.mark.usefixtures('left_menu_test_data')
    def test_edit(self, test_app, left_menu_test_data):
        role = left_menu_test_data['roles'][0]
        resp = self.get_item(test_app, role.id)
        self.check_left_menu(resp, 'Roles')
