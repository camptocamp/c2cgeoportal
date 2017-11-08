import pytest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertLeftMenuTestData(dbsession):
    from c2cgeoportal_commons.models.main import Role
    dbsession.begin_nested()
    dbsession.add(Role("secretary"))
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("test_app")
class TestLeftMenu():

    def _assert_main_menu(self, html, active_table=None):
        main_menus = html.find_all(id="main-menu")
        assert 1 == len(main_menus)
        active_lis = main_menus[0].find_all("li", "active")
        if active_table is None:
            assert 0 == len(active_lis)
        else:
            assert 1 == len(active_lis)
            active_links = active_lis[0].select("a[href$={}/]".format(active_table))
            assert 1 == len(active_links)

    def test_404(self, test_app):
        html = test_app.get("/this/is/notfound/", status=404).html
        self._assert_main_menu(html)

    def test_index(self, test_app):
        html = test_app.get("/roles/", status=200).html
        self._assert_main_menu(html, "roles")

    @pytest.mark.usefixtures("insertLeftMenuTestData")
    def test_edit(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Role
        role = dbsession.query(Role). \
            filter(Role.name == 'secretary'). \
            one()
        html = test_app.get("/roles/{}".format(role.id), status=200).html
        self._assert_main_menu(html, "roles")
