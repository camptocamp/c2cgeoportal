# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession', 'transact')
def left_menu_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Role

    roles = []
    role = Role('secretary')
    dbsession.add(role)
    roles.append(role)

    dbsession.flush()

    yield {
        'roles': roles
    }


@pytest.mark.usefixtures('test_app')
class TestLeftMenu(AbstractViewsTests):

    _prefix = '/roles'

    def test_index(self, test_app):
        resp = test_app.get('/roles', status=200)
        self.check_left_menu(resp, 'Roles')

    @pytest.mark.usefixtures('left_menu_test_data')
    def test_edit(self, test_app, left_menu_test_data):
        role = left_menu_test_data['roles'][0]
        resp = self.get_item(test_app, role.id)
        self.check_left_menu(resp, 'Roles')
