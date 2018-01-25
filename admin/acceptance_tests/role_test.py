# pylint: disable=no-self-use

import json
import re
import pytest
from pyramid.testing import DummyRequest

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import box, Polygon, shape

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
        role.extent = from_shape(box(485869.5728, 76443.1884, 837076.5648, 299941.7864),
                                 srid=21781)
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

        expected = Polygon([(1167544.3397631699, 5748064.729594703),
                            (1180453.0256760044, 6074797.96820131),
                            (658348.6696383564, 6080273.63626964),
                            (664577.4194513536, 5753148.2510447875),
                            (1167544.3397631699, 5748064.729594703)])
        assert expected.almost_equals(shape(json.loads(form['extent'].value)))

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
        form['extent'] = json.dumps({
            'type': 'Polygon',
            'coordinates': [[
                [1000000, 5800000],
                [1000000, 6000000],
                [700000, 6000000],
                [700000, 5800000],
                [1000000, 5800000]
            ]]
        })

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

        expected = Polygon([(719383.7988896352, 109062.8141734005),
                            (716689.3301397888, 245909.7643546755),
                            (513083.1504351135, 245400.5416369234),
                            (511073.1973649057, 108541.7344432737),
                            (719383.7988896352, 109062.8141734005)])
        assert expected.almost_equals(to_shape(role.extent))

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

    def test_unicity_validator(self, roles_test_data, test_app):
        role_proto = roles_test_data['roles'][7]
        resp = test_app.get("/roles/{}/duplicate".format(role_proto.id), status=200)

        resp = resp.form.submit('submit')

        AbstractViewsTests.check_one_submission_problem(
            '{} is already used.'.format(role_proto.name),
            resp)

    @pytest.mark.usefixtures('raise_db_error_on_query')
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        request = DummyRequest(dbsession=dbsession,
                               params={'current': 0, 'rowCount': 10})
        info = RoleViews(request).grid()
        assert info.status_int == 500, '500 status when db error'
