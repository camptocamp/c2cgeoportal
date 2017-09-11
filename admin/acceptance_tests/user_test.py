import pytest
from pyramid.testing import DummyRequest

@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertUsersTestData(dbsession):
    from c2cgeoportal_commons.models.main import User
    user = User("babar")
    dbsession.begin_nested()
    for i in range (0, 23):
        user = User("babar_" + str(i), email='mail' + str(i))
        dbsession.add(user)
    yield
    dbsession.rollback()

@pytest.mark.usefixtures("insertUsersTestData", "transact")
class TestUser():
    def test_view_index(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews
        info = UserViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'username'
        assert info['list_fields'][1][0] == 'email'
        assert type(info['list_fields'][1][1]) == str

    def test_view_edit(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews
        req = DummyRequest(dbsession=dbsession)
        req.matchdict.update({'id': '11'})
        info = UserViews(req).edit()
        import re

        clean_form = info['form'].replace('\n', ' ')
        while re.search('  ', clean_form, re.MULTILINE):
            clean_form = clean_form.replace('  ', ' ')
        clean_form = clean_form.replace(' >', '>')
        inputs = re.findall('<input type="text" .*?>', clean_form)

        assert inputs[0] == '<input type="text" name="username" value="babar_8" id="deformField3" class=" form-control "/>'
        assert inputs[3] == '<input type="text" name="email" value="mail8" id="deformField6" class=" form-control "/>'

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews
        request = DummyRequest(dbsession=dbsession, params={'current':0, 'rowCount':10})
        info = UserViews(request).grid()
        assert info.status_int == 500, '500 status when db error'

    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app(self, dbsession, test_app):
        res = test_app.get('/user/all/index', status=200)
        assert str(res.html.find_all('th', limit=3)) == \
             '[<th data-column-id="username">username</th>,' \
             + ' <th data-column-id="email">email</th>,' \
             + ' <th data-column-id="_id_" data-converter="commands" data-searchable="false" data-sortable="false">Commands</th>]'

    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        res = test_app.get('/user/all/index', status=200)
        res1 = res.click(verbose=True, href='language=fr')
        res2 = res1.follow()
        assert str(res2.html.find_all('th', limit=3)) == \
             '[<th data-column-id="username">username</th>,' \
             + ' <th data-column-id="email">mel</th>,' \
             + ' <th data-column-id="_id_" data-converter="commands" data-searchable="false" data-sortable="false">Actions</th>]'

    # in order to make this work, had to install selenium gecko driver
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium(self, selenium):
        selenium.get('http://127.0.0.1:6543' + '/user/all/index')
        elem = selenium.find_element_by_xpath("//a[contains(@href,'language=fr')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//button[@title='Actualiser']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(@href,'#50')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(@href,'13/edit')]")
        elem.click()
        pass
