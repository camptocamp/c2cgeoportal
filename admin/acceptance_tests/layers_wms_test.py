# pylint: disable=no-self-use

import pytest
from pyramid.testing import DummyRequest

from . import skip_if_travis, check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertLayerWMSTestData(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMS, OGCServer, RestrictionArea

    dbsession.begin_nested()
    servers = []
    for i in range(0, 4):
        servers.append(OGCServer(name='server_{}'.format(i)))
        dbsession.add(servers[i])
        dbsession.merge(servers[i])

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name="restrictionarea_{}".format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    for i in range(0, 25):
        layer = LayerWMS(name='layer_wms_{}'.format(i))
        layer.ogc_server_id = servers[i % 4].id
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]
        dbsession.add(layer)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("insertLayerWMSTestData", "transact", "test_app")
class TestLayerWMS():

    def test_view_index_rendering_in_app(self, test_app):
        expected = [('name', 'Name'),
                    ('metadata_url', 'Metadata URL'),
                    ('description', 'Description'),
                    ('public', 'Public'),
                    ('geo_table', 'Geo table'),
                    ('exclude_properties', 'Exclude properties'),
                    ('layer', 'WMS layer name'),
                    ('style', 'Style'),
                    ('time_mode', 'Time mode'),
                    ('time_widget', 'Time widget'),
                    ('ogc_server', 'OGC server'),
                    ('restrictionareas', 'Restriction areas'),
                    ('_id_', 'Commands')]
        check_grid_headers(test_app, '/layers_wms/', expected)

    def test_grid_complex_column_val(self, dbsession):
        from c2cgeoportal_admin.views.layers_wms import LayerWmsViews
        request = DummyRequest(dbsession=dbsession)
        request.params['rowCount'] = 1
        request.params['current'] = 1
        first_row = LayerWmsViews(request).grid()['rows'][0]
        assert 'restrictionarea_0, restrictionarea_2' == first_row['restrictionareas']
        assert 'server_0' == first_row['ogc_server']

    def test_left_menu(self, test_app):
        html = test_app.get("/layers_wms/", status=200).html
        main_menu = html.select_one('a[href="http://localhost/layers_wms/"]').getText()
        assert 'WMS Layers' == main_menu

    @skip_if_travis
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium(self, selenium):
        selenium.get('http://127.0.0.1:6544' + '/layers_wms/')

        elem = selenium.find_element_by_xpath("//a[contains(@href,'language=en')]")
        elem.click()

        elem = selenium.find_element_by_xpath("//div[@class='infos']")
        assert 'Showing 1 to 10 of 25 entries' == elem.text
        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()
