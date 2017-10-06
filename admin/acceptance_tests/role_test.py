import pytest
from . import clean_form
import re
import c2cgeoform
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


@pytest.mark.usefixtures("insertRolesTestData", "transact")
class TestRole():
    def test_view_index(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        info = RoleViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'name'
        assert type(info['list_fields'][0][1]) == str

    def test_view_edit(self, dbsession):
        c2cgeoform._set_widget_template_path()
        from c2cgeoportal_admin.views.roles import RoleViews
        req = DummyRequest(dbsession=dbsession)
        req.matchdict.update({'id': '11'})

        form = clean_form(RoleViews(req).edit()['form'])

        inputs = re.findall('<input type="text" .*?>', form)
        expected0 = ('<input'
                     ' type="text"'
                     ' name="name"'
                     ' value="secretary_10"'
                     ' id="deformField2"'
                     ' class=" form-control "/>')
        assert expected0 == inputs[0]
        expected1 = ('<input'
                     ' type="text"'
                     ' name="description"'
                     ' value=""'
                     ' id="deformField3"'
                     ' class=" form-control "/>')
        assert expected1 == inputs[1]

    @pytest.mark.usefixtures("test_app")  # route have to be registred for HTTP_FOUND
    def test_submit_update(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        post = {'__formid__': 'deform',
                '_charset_': 'UTF-8',
                'formsubmit': 'formsubmit',
                'id': '11',
                'name': 'secretary_with&&',
                'description': 'here is the fish',
                'extent': '',
                'functionalities': [],
                'restrictionareas': []
                }

        req = DummyRequest(dbsession=dbsession, post=post)
        req.matchdict.update({'id': '11'})
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
        res = test_app.get('/role/', status=200)
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
        res = test_app.get('/role/', status=200)
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
