# pylint: disable=no-self-use

import re
import pytest
from pyramid.testing import DummyRequest

from . import AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def roles_test_data(dbsession):
    from c2cgeoportal_commons.models.main import Role, Functionality, RestrictionArea
    dbsession.begin_nested()

    functionalities = {}
    for name in ('default_basemap', 'location'):
        functionalities[name] = []
        for v in range(0, 4):
            functionality = Functionality(
                name=name,
                value='value_{}'.format(v))
            dbsession.add(functionality)
            functionalities[name].append(functionality)

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name='restrictionarea_{}'.format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    roles = []
    for i in range(0, 23):
        role = Role('secretary_' + str(i))
        role.functionalities = [
            functionalities['default_basemap'][0],
            functionalities['location'][0],
            functionalities['location'][1]]
        role.restrictionareas = [
            restrictionareas[0],
            restrictionareas[1]]
        dbsession.add(role)
        roles.append(role)

    dbsession.flush()

    yield {
        'functionalities': functionalities,
        'restrictionareas': restrictionareas,
        'roles': roles
    }

    dbsession.rollback()


@pytest.mark.usefixtures('roles_test_data', 'transact', 'test_app')
class TestRole(AbstractViewsTests):

    _prefix = '/roles'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'Roles')

        expected = [('_id_', '', 'false'),
                    ('name', 'Name'),
                    ('description', 'Description'),
                    ('functionalities', 'Functionalities', 'false'),
                    ('restrictionareas', 'Restriction areas', 'false')]
        self.check_grid_headers(resp, expected)

    @pytest.mark.skip(reason='Translation is not finished')
    def test_index_rendering_fr(self, test_app):
        resp = self.get(test_app, locale='fr')

        self.check_left_menu(resp, 'Roles')

        expected = [('_id_', '', 'false'),
                    ('name', 'Name'),
                    ('description', 'Description'),
                    ('functionalities', 'Fonctionalités', 'false'),
                    ('restrictionareas', 'Aires de restriction', 'false')]
        self.check_grid_headers(resp, expected)

    def test_edit(self, dbsession, test_app, roles_test_data):
        role = roles_test_data['roles'][10]

        form = self.get_item(test_app, role.id).form

        assert 'secretary_10' == form['name'].value
        assert '' == form['description'].value

        functionalities = roles_test_data['functionalities']
        assert set((
            functionalities['default_basemap'][0].id,
            functionalities['location'][0].id,
            functionalities['location'][1].id
        )) == set(f.id for f in role.functionalities)
        self.check_checkboxes(
            form,
            'functionalities',
            [{
                'label': '{}={}'.format(f.name, f.value),
                'value': str(f.id),
                'checked': f in role.functionalities
            } for f in sum([roles_test_data['functionalities'][name]
                            for name in ('default_basemap', 'location')],
                           [])])

        ras = roles_test_data['restrictionareas']
        assert set((ras[0].id, ras[1].id)) == set(ra.id for ra in role.restrictionareas)
        self.check_checkboxes(
            form,
            'restrictionareas',
            [{
                'label': ra.name,
                'value': str(ra.id),
                'checked': ra in role.restrictionareas
            } for ra in sorted(ras, key=lambda ra: ra.name)])

        form['name'] = 'New name'
        form['description'] = 'New description'

        functionality_ids = [
            roles_test_data['functionalities']['default_basemap'][1].id,
            roles_test_data['functionalities']['location'][1].id,
            roles_test_data['functionalities']['default_basemap'][2].id]
        form['functionalities'] = [str(id) for id in functionality_ids]

        ra_ids = [
            roles_test_data['restrictionareas'][2].id,
            roles_test_data['restrictionareas'][3].id]
        form['restrictionareas'] = [str(id) for id in ra_ids]

        resp = form.submit('submit')

        assert str(role.id) == re.match('http://localhost/roles/(.*)', resp.location).group(1)

        dbsession.expire(role)

        assert 'New name' == role.name
        assert 'New description' == role.description

        assert set(functionality_ids) == set([f.id for f in role.functionalities])
        assert set(ra_ids) == set([f.id for f in role.restrictionareas])

    def test_duplicate(self, roles_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Role
        role_proto = roles_test_data['roles'][7]

        resp = test_app.get("/roles/{}/duplicate".format(role_proto.id), status=200)
        form = resp.form

        assert '' == form['id'].value
        assert role_proto.name == form['name'].value
        assert role_proto.description == form['description'].value
        form['name'].value = 'clone'
        resp = form.submit('submit')

        role = dbsession.query(Role).filter(Role.name == 'clone').one()
        assert str(role.id) == re.match('http://localhost/roles/(.*)', resp.location).group(1)
        assert role_proto.id != role.id
        assert role_proto.functionalities[2].name == role.functionalities[2].name
        assert role_proto.functionalities[2].value == role.functionalities[2].value
        assert role_proto.functionalities[2].id == role.functionalities[2].id
        assert role_proto.restrictionareas[1].name == role.restrictionareas[1].name
        assert role_proto.restrictionareas[1].id == role.restrictionareas[1].id

    @pytest.mark.usefixtures('raise_db_error_on_query')
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        request = DummyRequest(dbsession=dbsession,
                               params={'current': 0, 'rowCount': 10})
        info = RoleViews(request).grid()
        assert info.status_int == 500, '500 status when db error'
