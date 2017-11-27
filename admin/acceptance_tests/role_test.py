# pylint: disable=no-self-use

import re
import pytest
from pyramid.testing import DummyRequest

from . import check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def roles_test_data(dbsession):
    from c2cgeoportal_commons.models.main import Role, Functionality, RestrictionArea
    dbsession.begin_nested()

    functionalities = {}
    for name in ("default_basemap", "location"):
        functionalities[name] = []
        for v in range(0, 4):
            functionality = Functionality(
                name=name,
                value="value_{}".format(v))
            dbsession.add(functionality)
            functionalities[name].append(functionality)

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name="restrictionarea_{}".format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    roles = []
    for i in range(0, 23):
        role = Role("secretary_" + str(i))
        role.functionalities = [
            functionalities["default_basemap"][0],
            functionalities["location"][0],
            functionalities["location"][1]]
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


@pytest.mark.usefixtures("roles_test_data", "transact", "test_app")
class TestRole():

    def test_view_index(self, test_app):
        test_app.get('/roles/', status=200)

    def test_view_index_list_fields(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        info = RoleViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'name'

    def test_edit(self, dbsession, test_app, roles_test_data):
        role = roles_test_data['roles'][10]

        resp = test_app.get('/roles/{}'.format(role.id), status=200)
        form = resp.form

        assert "secretary_10" == form['name'].value
        assert "" == form['description'].value

        # functionalities
        form_group = resp.html.select_one(".item-functionalities")

        functionalities_labels = form_group.select(".checkbox label")
        for i, functionality in enumerate(sum([roles_test_data['functionalities'][name]
                                               for name in ("default_basemap", "location")], [])):
            label = functionalities_labels[i]
            checkbox = label.select_one("input")

            assert ["{}={}".format(functionality.name, functionality.value)] == \
                list(label.stripped_strings)
            assert str(functionality.id) == checkbox["value"]
            if functionality in role.functionalities:
                assert "True" == checkbox["checked"]
                assert form.get("functionalities", index=i).checked
            else:
                assert "checked" not in checkbox
                assert not form.get("functionalities", index=i).checked

        # restrictionareas
        form_group = resp.html.select_one(".item-restrictionareas")
        ra_labels = form_group.select(".checkbox label")
        for i, ra in enumerate(roles_test_data['restrictionareas']):
            label = ra_labels[i]
            checkbox = label.select_one("input")
            assert [ra.name] == list(label.stripped_strings)
            assert str(ra.id) == checkbox["value"]
            if ra in role.restrictionareas:
                assert "True" == checkbox["checked"]
                assert form.get("restrictionareas", index=i).checked
            else:
                assert "checked" not in checkbox
                assert not form.get("restrictionareas", index=i).checked

        form["name"] = "New name"
        form["description"] = "New description"

        functionality_ids = [
            roles_test_data['functionalities']['default_basemap'][1].id,
            roles_test_data['functionalities']['location'][1].id,
            roles_test_data['functionalities']['default_basemap'][2].id]
        form["functionalities"] = [str(id) for id in functionality_ids]

        ra_ids = [
            roles_test_data['restrictionareas'][2].id,
            roles_test_data['restrictionareas'][3].id]
        form["restrictionareas"] = [str(id) for id in ra_ids]

        resp = form.submit("submit")

        assert str(role.id) == re.match('http://localhost/roles/(.*)', resp.location).group(1)

        dbsession.expire(role)

        assert "New name" == role.name
        assert "New description" == role.description

        assert set(functionality_ids) == set([f.id for f in role.functionalities])
        assert set(ra_ids) == set([f.id for f in role.restrictionareas])

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        request = DummyRequest(dbsession=dbsession,
                               params={'current': 0, 'rowCount': 10})
        info = RoleViews(request).grid()
        assert info.status_int == 500, '500 status when db error'

    def test_view_index_rendering_in_app(self, dbsession, test_app):
        expected = [('_id_', ''),
                    ('name', 'Name'),
                    ('description', 'Description'),
                    ('functionalities', 'Functionalities'),
                    ('restrictionareas', 'Restriction areas')]
        check_grid_headers(test_app, '/roles/', expected)

    @pytest.mark.skip(reason="Translation is not finished")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        expected = [('_id_', ''),
                    ('name', 'name'),
                    ('description', 'Description'),
                    ('functionalities', 'Functionalités'),
                    ('restrictionareas', 'Zones autorisées')]
        check_grid_headers(test_app, '/roles/', expected, language='en')
