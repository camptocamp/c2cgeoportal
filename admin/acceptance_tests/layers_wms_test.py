# pylint: disable=no-self-use

import pytest
from pyramid.testing import DummyRequest

from . import skip_if_ci, check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def layer_wms_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMS, OGCServer, RestrictionArea, LayergroupTreeitem, \
        Interface, Dimension, Metadata, LayerGroup

    dbsession.begin_nested()
    servers = []
    for i in range(0, 4):
        servers.append(OGCServer(name='server_{}'.format(i)))
        dbsession.add(servers[i])

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name="restrictionarea_{}".format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    interfaces = [Interface(name) for name
                  in ["desktop", "mobile", "edit", "routing"]]
    for interface in interfaces:
        dbsession.add(interface)

    dimensions_protos = [("Date", "2017"),
                         ("Date", "2018"),
                         ("Date", "1988"),
                         ("CLC", "all"), ]
    metadatas_protos = [("copyable", "true"),
                        ("disclaimer", "© le momo"),
                        ("snappingConfig", '{"tolerance": 50}')]
    groups = []
    for i in range(0, 5):
        group = LayerGroup(name='layer_group_{}'.format(i))
        groups.append(group)
        dbsession.add(group)

    layers = []
    for i in range(0, 25):
        layer = LayerWMS(name='layer_wms_{}'.format(i))
        layer.public = 1 == i % 2
        layer.ogc_server = servers[i % 4]
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]
        layer.interfaces = [interfaces[i % 4],
                            interfaces[(i + 2) % 4]]

        layer.dimensions = [Dimension(name=dimensions_protos[id][0],
                                      value=dimensions_protos[id][1],
                                      layer=layer)
                            for id in [i % 3, (i + 2) % 4, (i + 3) % 4]]

        layer.metadatas = [Metadata(name=metadatas_protos[id][0],
                                    value=metadatas_protos[id][1])
                           for id in [i % 3, (i + 2) % 3]]
        for metadata in layer.metadatas:
            metadata.item = layer

        dbsession.add(LayergroupTreeitem(group=groups[i % 5],
                                         item=layer,
                                         ordering=len(groups[i % 5].children_relation)))
        dbsession.add(LayergroupTreeitem(group=groups[(i + 3) % 5],
                                         item=layer,
                                         ordering=len(groups[(i + 3) % 5].children_relation)))

        dbsession.add(layer)
        layers.append(layer)

    yield {
        "servers": servers,
        "restrictionareas": restrictionareas,
        "layers": layers,
        "interfaces": interfaces
    }

    dbsession.rollback()


@pytest.mark.usefixtures("layer_wms_test_data", "transact", "test_app")
class TestLayerWMS():

    def test_view_index_rendering_in_app(self, test_app):
        expected = [('_id_', '', 'false'),
                    ('name', 'Name'),
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
                    ('interfaces', "Interfaces", 'false'),
                    ('dimensions', "Dimensions", 'false'),
                    ('parents_relation', "Parents", 'false'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        check_grid_headers(test_app, '/layers_wms/', expected)

    def test_grid_complex_column_val(self, dbsession):
        from c2cgeoportal_admin.views.layers_wms import LayerWmsViews
        request = DummyRequest(dbsession=dbsession)
        request.params['rowCount'] = 1
        request.params['current'] = 1
        first_row = LayerWmsViews(request).grid()['rows'][0]

        assert 'server_0' == first_row['ogc_server']
        assert 'desktop, edit' == first_row['interfaces']
        assert 'Date: 2017, 1988; CLC: all' == first_row['dimensions']
        assert 'layer_group_0, layer_group_3' == first_row['parents_relation']
        assert 'restrictionarea_0, restrictionarea_2' == first_row['restrictionareas']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == first_row['metadatas']

    def test_left_menu(self, test_app):
        html = test_app.get("/layers_wms/", status=200).html
        main_menu = html.select_one('a[href="http://localhost/layers_wms/"]').getText()
        assert 'WMS Layers' == main_menu

    def test_base_edit(self, test_app, layer_wms_test_data):
        layer = layer_wms_test_data['layers'][10]
        resp = test_app.get('/layers_wms/{}'.format(layer.id), status=200)
        form = resp.form

        assert "layer_wms_10" == form['name'].value
        assert "" == form['description'].value

    def test_public_checkbox_edit(self, test_app, layer_wms_test_data):
        layer = layer_wms_test_data['layers'][10]
        form10 = test_app.get('/layers_wms/{}'.format(layer.id), status=200).form
        assert not form10['public'].checked
        layer = layer_wms_test_data['layers'][11]
        form11 = test_app.get('/layers_wms/{}'.format(layer.id), status=200).form
        assert form11['public'].checked

    @skip_if_ci
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_selenium(self, selenium, selenium_app):
        selenium.get(selenium_app + '/layers_wms/')

        elem = selenium.find_element_by_xpath("//a[contains(@href,'language=en')]")
        elem.click()

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions
        elem = WebDriverWait(selenium, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, "//div[@class='infos']")))
        assert 'Showing 1 to 10 of 25 entries' == elem.text
        elem = selenium.find_element_by_xpath("//button[@title='Refresh']/following-sibling::*")
        elem.click()
        elem = selenium.find_element_by_xpath("//a[contains(.,'50')]")
        elem.click()
