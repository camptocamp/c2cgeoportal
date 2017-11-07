import pytest
from pyramid.testing import DummyRequest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertRolesTestData(dbsession):
    from c2cgeoportal_commons.models.main import Role
    dbsession.begin_nested()
    for i in range(0, 23):
        role = Role("secretary_" + str(i))
        dbsession.add(role)
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
        assert type(info['list_fields'][0][1]) == str

    def test_view_edit(self, dbsession, test_app):
        role = self._role_by_name(dbsession, 'secretary_10')
        resp = test_app.get('/roles/{}/edit'.format(role.id), status=200)
        assert resp.form['name'].value == "secretary_10"
        assert resp.form['description'].value == ""

    # route have to be registred for HTTP_FOUND
    @pytest.mark.usefixtures("test_app")
    def test_submit_update(self, dbsession):
        role = self._role_by_name(dbsession, 'secretary_11')
        from c2cgeoportal_admin.views.roles import RoleViews
        post = {'__formid__': 'deform',
                '_charset_': 'UTF-8',
                'formsubmit': 'formsubmit',
                'id': str(role.id),
                'name': 'secretary_with&&',
                'description': 'here is the fish',
                'extent': '',
                'functionalities': [],
                'restrictionareas': []
                }

        req = DummyRequest(dbsession=dbsession, post=post)
        req.matchdict.update({'id': str(role.id)})
        req.matchdict.update({'table': 'role'})

        RoleViews(req).save()

        from c2cgeoportal_commons.models.main import Role
        role = dbsession.query(Role). \
            filter(Role.name == 'secretary_with&&'). \
            one_or_none()
        assert role.description == 'here is the fish'

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        request = DummyRequest(dbsession=dbsession,
                               params={'current': 0, 'rowCount': 10})
        info = RoleViews(request).grid()
        assert info.status_int == 500, '500 status when db error'

    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app(self, dbsession, test_app):
        res = test_app.get('/roles/', status=200)
        res1 = res.click(verbose=True, href='language=en')
        res2 = res1.follow()
        expected = ('[<th data-column-id="name">name</th>,'
                    ' <th data-column-id="_id_"'
                    ' data-converter="commands"'
                    ' data-searchable="false"'
                    ' data-sortable="false">Commands</th>]')
        assert expected == str(res2.html.find_all('th', limit=2))
        assert 1 == len(list(filter(lambda x: str(x.contents) == "['New']",
                                    res2.html.findAll('a'))))

    @pytest.mark.skip(reason="Translation is not finished")
    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        res = test_app.get('/roles/', status=200)
        res1 = res.click(verbose=True, href='language=fr')
        res2 = res1.follow()
        expected = ('[<th data-column-id="name">nom</th>,'
                    ' <th data-column-id="_id_"'
                    ' data-converter="commands"'
                    ' data-searchable="false"'
                    ' data-sortable="false">Actions</th>]')
        assert expected == str(res2.html.find_all('th', limit=2))
        assert 1 == len(list(filter(lambda x: str(x.contents) == "['Nouveau']",
                                    res2.html.findAll('a'))))
