# pylint: disable=no-self-use


import json
import pytest
import re
from geoalchemy2.shape import from_shape
from shapely.geometry import box, Polygon, shape

from . import AbstractViewsTests


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession', 'transact')
def restriction_area_test_data(dbsession, transact):
    del transact
    from c2cgeoportal_commons.models.main import RestrictionArea, Role

    roles = []
    for i in range(0, 4):
        roles.append(Role("secretary_" + str(i)))
        dbsession.add(roles[i])

    restrictionareas = []
    for i in range(0, 4):
        restrictionarea = RestrictionArea(name='restrictionarea_{}'.format(i))
        restrictionarea.area = \
            from_shape(box(485869.5728, 76443.1884, 837076.5648, 299941.7864), srid=21781)
        restrictionarea.description = 'description_{}'.format(i)
        restrictionarea.roles = [roles[i % 4], roles[(i + 2) % 4]]
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    dbsession.flush()
    yield {
        'restriction_areas': restrictionareas,
        'roles': roles
    }


@pytest.mark.usefixtures('restriction_area_test_data', 'test_app')
class TestRestrictionAreaViews(AbstractViewsTests):

    _prefix = '/restriction_areas'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'Restriction areas')

        expected = [('actions', '', 'false'),
                    ('id', 'id', 'true'),
                    ('name', 'Name', 'true'),
                    ('description', 'Description', 'true'),
                    ('readwrite', 'Read/write', 'true'),
                    ('roles', 'Roles', 'false'),
                    ('layers', 'Layers', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app):
        self.check_search(test_app, 'restrictionarea_1', total=1)

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import RestrictionArea

        resp = test_app.post(
            '/restriction_areas/new',
            {
                'name': 'new_name',
                'description': 'new_description'
            },
            status=302)

        restriction_area = dbsession.query(RestrictionArea). \
            filter(RestrictionArea.name == 'new_name').one()
        assert str(restriction_area.id) == \
            re.match(
                'http://localhost/restriction_areas/(.*)\?msg_col=submit_ok',
                resp.location).group(1)
        assert restriction_area.name == 'new_name'

    def test_unicity_validator(self, restriction_area_test_data, test_app):
        restriction_area = restriction_area_test_data['restriction_areas'][2]

        resp = test_app.get("/restriction_areas/{}/duplicate".format(restriction_area.id), status=200)
        resp = resp.form.submit('submit')

        self._check_submission_problem(resp, '{} is already used.'.format(restriction_area.name))

    def test_edit(self, test_app, restriction_area_test_data, dbsession):
        restriction_area = restriction_area_test_data['restriction_areas'][0]
        roles = restriction_area_test_data['roles']

        form = self.get_item(test_app, restriction_area.id).form

        assert str(restriction_area.id) == self.get_first_field_named(form, 'id').value
        assert 'hidden' == self.get_first_field_named(form, 'id').attrs['type']
        assert restriction_area.name == form['name'].value
        expected = Polygon([(1167544.3397631699, 5748064.729594703),
                            (1180453.0256760044, 6074797.96820131),
                            (658348.6696383564, 6080273.63626964),
                            (664577.4194513536, 5753148.2510447875),
                            (1167544.3397631699, 5748064.729594703)])
        assert expected.almost_equals(shape(json.loads(form['area'].value)))
        self._check_roles(form, roles, restriction_area)

        form['description'] = 'new_description'
        form['roles'] = [roles[i].id for i in range(0, 3)]
        form.submit('submit')

        dbsession.expire(restriction_area)
        assert restriction_area.description == 'new_description'
        assert set(restriction_area.roles) == set([roles[i] for i in range(0, 3)])

    def test_delete(self, test_app, restriction_area_test_data, dbsession):
        from c2cgeoportal_commons.models.main import RestrictionArea

        restriction_area = restriction_area_test_data['restriction_areas'][0]
        deleted_id = restriction_area.id
        test_app.delete('/restriction_areas/{}'.format(deleted_id), status=200)
        assert dbsession.query(RestrictionArea).get(deleted_id) is None

    def test_duplicate(self, restriction_area_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import RestrictionArea
        restriction_area = restriction_area_test_data['restriction_areas'][3]
        roles = restriction_area_test_data['roles']

        form = test_app.get("/restriction_areas/{}/duplicate".format(restriction_area.id), status=200).form

        assert '' == self.get_first_field_named(form, 'id').value
        self._check_roles(form, roles, restriction_area)

        self.set_first_field_named(form, 'name', 'clone')
        resp = form.submit('submit')

        assert resp.status_int == 302
        restriction_area = dbsession.query(RestrictionArea).filter(RestrictionArea.name == 'clone').one()
        assert str(restriction_area.id) == \
            re.match(
                'http://localhost/restriction_areas/(.*)\?msg_col=submit_ok',
                resp.location).group(1)
