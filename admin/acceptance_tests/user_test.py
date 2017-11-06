import pytest
from pyramid.testing import DummyRequest
from selenium.common.exceptions import NoSuchElementException

from . import skip_if_travis


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertUsersTestData(dbsession):
    from c2cgeoportal_commons.models.static import User
    from c2cgeoportal_commons.models.main import Role
    dbsession.begin_nested()
    roles = []
    for i in range(0, 4):
        roles.append(Role("secretary_" + str(i)))
        dbsession.add(roles[i])
    for i in range(0, 23):
        user = User("babar_" + str(i),
                    email='mail' + str(i),
                    role=roles[i % 4])
        dbsession.add(user)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("insertUsersTestData", "transact", "test_app")
class TestUser():
    def test_view_index(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews
        info = UserViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'username'
        assert info['list_fields'][1][0] == 'email'
        assert type(info['list_fields'][1][1]) == str

    def test_view_edit(self, dbsession, test_app):
        from c2cgeoportal_commons.models.static import User
        user = dbsession.query(User). \
            filter(User.username == 'babar_9'). \
            one()

        resp = test_app.get('/users/{}'.format(user.id), status=200)

        assert resp.form['username'].value == user.username
        assert resp.form['email'].value == user.email
        assert resp.form['role_name'].options == [
            ('', False, '- Select -'),
            ('secretary_0', False, 'secretary_0'),
            ('secretary_1', True, 'secretary_1'),
            ('secretary_2', False, 'secretary_2'),
            ('secretary_3', False, 'secretary_3')]
        assert resp.form['role_name'].value == user.role_name

    def test_delete_success(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        user_id = dbsession.query(User). \
            filter(User.username == 'babar_9'). \
            one().id
        from c2cgeoportal_admin.views.users import UserViews
        req = DummyRequest(dbsession=dbsession)
        req.matchdict.update({'id': str(user_id)})

        UserViews(req).delete()

        user = dbsession.query(User).filter(User.id == user_id).one_or_none()
        assert user is None

    @pytest.mark.usefixtures("test_app")
    def test_submit_update(self, dbsession, test_app):
        from c2cgeoportal_commons.models.static import User
        user = dbsession.query(User). \
            filter(User.username == 'babar_11'). \
            one()

        resp = test_app.post(
            '/users/{}'.format(user.id),
            {
                '__formid__': 'deform',
                '_charset_': 'UTF-8',
                'formsubmit': 'formsubmit',
                'item_type': 'user',
                'id': user.id,
                'username': 'new_name_withéàô',
                'email': 'new_mail',
                'role_name': 'secretary_2',
                'is_password_changed': 'false',
                '_password': 'da39a3ee5e6b4b0d3255bfef95601890afd80709',
                'temp_password': ''},
            status=302)
        assert resp.location == 'http://localhost/users/{}'.format(user.id)

        dbsession.expire(user)
        assert user.username == 'new_name_withéàô'
        assert user.email == 'new_mail'
        assert user.role_name == 'secretary_2'

    @pytest.mark.usefixtures("test_app")
    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.static import User

        resp = test_app.post(
            '/users/new',
            {
                '__formid__': 'deform',
                '_charset_': 'UTF-8',
                'formsubmit': 'formsubmit',
                'item_type': 'user',
                'id': '',
                'username': 'new_user',
                'email': 'new_mail',
                'role_name': 'secretary_2',
                'is_password_changed': 'false',
                '_password': 'da39a3ee5e6b4b0d3255bfef95601890afd80709',
                'temp_password': ''},
            status=302)

        import re
        assert re.match('http://localhost/users/.[0-9]', resp.location)

        user = dbsession.query(User). \
            filter(User.username == 'new_user'). \
            one()
        dbsession.expire(user)
        assert user.username == 'new_user'
        assert user.email == 'new_mail'
        assert user.role_name == 'secretary_2'


    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews
        request = DummyRequest(dbsession=dbsession,
                               params={'current': 0, 'rowCount': 10})
        info = UserViews(request).grid()
        assert info.status_int == 500, '500 status when db error'

    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app(self, dbsession, test_app):
        res = test_app.get('/users/', status=200)
        res1 = res.click(verbose=True, href='language=en')
        res2 = res1.follow()
        expected = ('[<th data-column-id="username">username</th>,'
                    ' <th data-column-id="email">email</th>,'
                    ' <th data-column-id="_id_"'
                    ' data-converter="commands"'
                    ' data-searchable="false"'
                    ' data-sortable="false">Commands</th>]')
        assert expected == str(res2.html.find_all('th', limit=3))
        assert 1 == len(list(filter(lambda x: str(x.contents) == "['New']",
                                    res2.html.findAll('a'))))

    @pytest.mark.skip(reason="Translation is not finished")
    @pytest.mark.usefixtures("test_app")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        res = test_app.get('/users/', status=200)
        res1 = res.click(verbose=True, href='language=fr')
        res2 = res1.follow()
        expected = ('[<th data-column-id="username">username</th>,'
                    ' <th data-column-id="email">mel</th>,'
                    ' <th data-column-id="_id_"'
                    ' data-converter="commands"'
                    ' data-searchable="false"'
                    ' data-sortable="false">Actions</th>]')
        assert expected == str(res2.html.find_all('th', limit=3))
        assert 1 == len(list(filter(lambda x: str(x.contents) == "['Nouveau']",
                                    res2.html.findAll('a'))))

    # in order to make this work, had to install selenium gecko driver
    @skip_if_travis
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium(self, dbsession, selenium):
        selenium.get('http://127.0.0.1:6543/users/')

        # elem = selenium.find_element_by_xpath(
        #     "//a[contains(@href,'language=fr')]")
        # elem.click()

        grid_header = selenium.find_element_by_xpath("//div[contains(@id,'grid-header')]")
        elem = grid_header.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = grid_header.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()

        from c2cgeoportal_commons.models.static import User
        user = dbsession.query(User). \
            filter(User.username == 'babar_13'). \
            one()

        elem = selenium.find_element_by_xpath("//a[contains(@href,'{}')]".format(user.id))
        elem.click()
        elem = selenium.find_element_by_xpath("//input[@name ='username']")
        elem.clear()
        elem.send_keys('new_name_éôù')
        elem = selenium.find_element_by_xpath("//input[@name ='email']")
        elem.clear()
        elem.send_keys('new_email')

        elem = selenium.find_element_by_xpath("//button[@name='formsubmit']")
        elem.click()

        dbsession.expire(user)
        assert user.username == 'new_name_éôù'
        assert user.email == 'new_email'

    # in order to make this work, had to install selenium gecko driver
    @skip_if_travis
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_delete_selenium(self, dbsession, selenium):
        from c2cgeoportal_commons.models.static import User
        user_id = dbsession.query(User). \
            filter(User.username == 'babar_13'). \
            one().id
        selenium.get('http://127.0.0.1:6543' + '/users/')

        elem = selenium.find_element_by_xpath("//div[@class='infos']")
        assert 'Showing 1 to 10 of 23 entries' == elem.text
        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(@href,'{}')]/following-sibling::*"
                                              .format(user_id))
        elem.click()
        selenium.switch_to_alert().accept()

        selenium.switch_to_default_content()
        selenium.refresh()
        elem = selenium.find_element_by_xpath("//div[@class='infos']")
        assert 'Showing 1 to 10 of 22 entries' == elem.text
        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()
        with pytest.raises(NoSuchElementException):
            selenium.find_element_by_xpath("//a[contains(@href,'{}')]/following-sibling::*"
                                           .format(user_id))
