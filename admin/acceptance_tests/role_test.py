# pylint: disable=no-self-use

import re
import pytest
from pyramid.testing import DummyRequest

from . import check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertRolesTestData(dbsession):
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

    dbsession.flush()

    yield

    dbsession.rollback()


@pytest.mark.usefixtures("insertRolesTestData", "transact", "test_app")
class TestRole():

    def _role_by_name(self, dbsession, name):
        from c2cgeoportal_commons.models.main import Role
        role = dbsession.query(Role). \
            filter(Role.name == name). \
            one()
        return role

    def test_view_index(self, test_app):
        test_app.get('/roles/', status=200)

    def test_view_index_list_fields(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        info = RoleViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'name'

    def _functionality(self, dbsession, name, value):
        from c2cgeoportal_commons.models.main import Functionality
        return dbsession.query(Functionality). \
            filter(Functionality.name == name). \
            filter(Functionality.value == value). \
            one_or_none()

    def _restrictionarea(self, dbsession, name):
        from c2cgeoportal_commons.models.main import RestrictionArea
        return dbsession.query(RestrictionArea). \
            filter(RestrictionArea.name == name). \
            one_or_none()

    def test_edit(self, dbsession, test_app):
        role = self._role_by_name(dbsession, 'secretary_10')

        resp = test_app.get('/roles/{}'.format(role.id), status=200)
        form = resp.form

        assert "secretary_10" == form['name'].value
        assert "" == form['description'].value

        # functionalities
        from c2cgeoportal_commons.models.main import Functionality
        form_group = resp.html.select_one(".item-functionalities")
        functionalities = dbsession.query(Functionality). \
            order_by(Functionality.name, Functionality.value). \
            all()
        functionalities_labels = form_group.select(".checkbox label")
        for i, functionality in enumerate(functionalities):
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
        from c2cgeoportal_commons.models.main import RestrictionArea
        form_group = resp.html.select_one(".item-restrictionareas")
        ras = dbsession.query(RestrictionArea). \
            order_by(RestrictionArea.name). \
            all()
        ra_labels = form_group.select(".checkbox label")
        for i, ra in enumerate(ras):
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

        functionality_ids = [f.id for f in [
            self._functionality(dbsession, 'default_basemap', 'value_1'),
            self._functionality(dbsession, 'location', 'value_1'),
            self._functionality(dbsession, 'default_basemap', 'value_2')]]
        form["functionalities"] = [str(id) for id in functionality_ids]

        ra_ids = [ra.id for ra in [
            self._restrictionarea(dbsession, 'restrictionarea_2'),
            self._restrictionarea(dbsession, 'restrictionarea_3')]]
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
                    ('name', 'name'),
                    ('description', 'description'),
                    ('functionalities', 'functionalities'),
                    ('restrictionareas', 'restrictionareas')]
        check_grid_headers(test_app, '/roles/', expected)

    @pytest.mark.skip(reason="Translation is not finished")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        expected = [('_id_', ''),
                    ('name', 'name'),
                    ('description', 'description'),
                    ('functionalities', 'functionalitiés'),
                    ('restrictionareas', 'zones autorisées')]
        check_grid_headers(test_app, '/roles/', expected, language='en')
