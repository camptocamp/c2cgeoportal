# pylint: disable=no-self-use

import pytest
import re
from pyramid.testing import DummyRequest
from selenium.common.exceptions import NoSuchElementException

from . import skip_if_travis, check_grid_headers


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
        user.password = 'pré$ident'
        dbsession.add(user)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("insertUsersTestData", "transact", "test_app")
class TestUser():
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
                'role_name': 'secretary_2'},
            status=302)
        assert resp.location == 'http://localhost/users/{}'.format(user.id)

        dbsession.expire(user)
        assert user.username == 'new_name_withéàô'
        assert user.email == 'new_mail'
        assert user.role_name == 'secretary_2'
        assert user.validate_password('pré$ident')

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

        user = dbsession.query(User). \
            filter(User.username == 'new_user'). \
            one()

        assert str(user.id) == re.match('http://localhost/users/(.*)', resp.location).group(1)

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

    def test_view_index_rendering_in_app(self, dbsession, test_app):
        expected = [('_id_', ''),
                    ('username', 'username'),
                    ('role_name', 'role'),
                    ('email', 'email')]
        check_grid_headers(test_app, '/users/', expected)

    @pytest.mark.skip(reason="Translation is not finished")
    def test_view_index_rendering_in_app_fr(self, dbsession, test_app):
        expected = [('_id_', ''),
                    ('username', 'nom'),
                    ('role_name', 'role'),
                    ('email', 'mel')]
        check_grid_headers(test_app, '/users/', expected, language='fr')

    # in order to make this work, had to install selenium gecko driver
    @skip_if_travis
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium(self, dbsession, selenium, selenium_app):
        selenium.get(selenium_app + '/users/')

        elem = selenium.find_element_by_xpath("//a[contains(@href,'language=en')]")
        elem.click()

        grid_header = selenium.find_element_by_xpath("//div[contains(@id,'grid-header')]")
        elem = grid_header.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = grid_header.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()

        from c2cgeoportal_commons.models.static import User
        user = dbsession.query(User). \
            filter(User.username == 'babar_13'). \
            one()

        elem = selenium.find_element_by_xpath("//a[@href='{}/users/{}']".format(selenium_app, user.id))
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
    def test_delete_selenium(self, dbsession, selenium, selenium_app):
        from c2cgeoportal_commons.models.static import User
        user_id = dbsession.query(User). \
            filter(User.username == 'babar_13'). \
            one().id
        selenium.get(selenium_app + '/users/')

        elem = selenium.find_element_by_xpath("//a[contains(@href,'language=en')]")
        elem.click()

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        elem = WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='infos']")))
        assert 'Showing 1 to 10 of 23 entries' == elem.text
        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[@data-url='{}/users/{}']"
                                              .format(selenium_app, user_id))
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
            selenium.find_element_by_xpath("//a[@data-url='{}/users/{}')]"
                                           .format(selenium_app, user_id))
