import pytest
from . import clean_form
import re
import c2cgeoform
from pyramid.testing import DummyRequest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertRolesTestData(dbsession):
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.main import RestrictionArea
    from c2cgeoportal_commons.models.main import RestrictionAreaForRole
    dbsession.begin_nested()
    restrictionAreaList = []
    for i in range(0, 8):
        restrictionArea = RestrictionArea(
            name="ra_" + str(i),
            description="ra_desc_" + str(i))
        restrictionArea = dbsession.merge(restrictionArea)
        dbsession.flush()
        restrictionAreaList.append(restrictionArea.id)
    for i in range(0, 23):
        role = Role("secretary_" + str(i))
        role = dbsession.merge(role)
        dbsession.flush()
        rafr = RestrictionAreaForRole()
        rafr.role_id = role.id
        rafr.restrictionarea_id = restrictionAreaList[i % 8]
        dbsession.add(rafr)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("insertRolesTestData", "transact")
class TestRole():
    def test_view_index(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews
        info = RoleViews(DummyRequest(dbsession=dbsession)).index()
        assert info['list_fields'][0][0] == 'name'
        assert type(info['list_fields'][0][1]) == str

    @pytest.mark.usefixtures("test_app")
    def test_view_edit(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import Role
        role = dbsession.query(Role). \
            filter(Role.name == 'secretary_3').one()

        resp = test_app.get('/role/{}/edit'.format(role.id), status=200)
        assert role.name == resp.form['name'].value
        assert '' == resp.form['description'].value
        expected_ra = {
            '7': 'ra_6',
            '6': 'ra_5',
            '4': 'ra_3',
            '1': 'ra_0',
            '3': 'ra_2',
            '2': 'ra_1',
            '8': 'ra_7',
            '5': 'ra_4'}
        assert expected_ra == {c['value']: (next(c.parent.stripped_strings))
                               for c in resp.html.find_all('input', {'name': 'checkbox'})}
        assert '4' == resp.html.find('input', {'name': 'checkbox', 'checked': 'True'})['value']

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
                'restrictionareas': ['3', '4']
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
        from c2cgeoportal_commons.models.main import RestrictionAreaForRole
        rafrs = dbsession.query(RestrictionAreaForRole). \
            filter(RestrictionAreaForRole.role_id == role.id).all()
        ra1, ra2 = (rafr.restrictionarea_id for rafr in rafrs)
        assert (3, 4) == (ra1, ra2)

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

    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium_ra(self, dbsession, selenium):
        selenium.get('http://127.0.0.1:6543' + '/role/')
        # elem = selenium.find_element_by_xpath("//a[contains(@href,'language=fr')]")
        # elem.click()

        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(@href,'#50')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(@href,'13/edit')]")
        elem.click()
        elem = selenium.find_element_by_xpath("//input[@name ='checkbox'][@checked = 'True']")
        elem.click()
        elem = selenium.find_element_by_xpath("//label[contains(.,'ra_0')]/input")
        elem.click()
        elem = selenium.find_element_by_xpath("//label[contains(.,'ra_1')]/input")
        elem.click()
        elem = selenium.find_element_by_xpath("//button[@name='formsubmit']")
        elem.click()

        name = selenium.find_element_by_xpath("//input[@name ='name']").get_attribute("value")
        from c2cgeoportal_commons.models.main import Role
        role = dbsession.query(Role). \
            filter(Role.name == name). \
            one_or_none()
        from c2cgeoportal_commons.models.main import RestrictionAreaForRole
        rafrs = dbsession.query(RestrictionAreaForRole). \
            filter(RestrictionAreaForRole.role_id == role.id).all()
        ras_id = [rafr.restrictionarea_id for rafr in rafrs]
        from c2cgeoportal_commons.models.main import RestrictionArea
        ras = dbsession.query(RestrictionArea). \
            filter(RestrictionArea.id.in_(ras_id)).all()
        (n1, n2) = (ra.name for ra in ras)
        assert ('ra_0', 'ra_1') == (n1, n2)
