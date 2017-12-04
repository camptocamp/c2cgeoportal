# pylint: disable=no-self-use

import re
import pytest

from . import skip_if_ci, check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def layer_wms_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMS, OGCServer, RestrictionArea, LayergroupTreeitem, \
        Interface, Dimension, Metadata, LayerGroup

    dbsession.begin_nested()

    servers = [OGCServer(name='server_{}'.format(i)) for i in range(0, 4)]

    restrictionareas = [RestrictionArea(name="restrictionarea_{}".format(i))
                        for i in range(0, 5)]

    interfaces = [Interface(name) for name in ["desktop", "mobile", "edit", "routing"]]

    dimensions_protos = [("Date", "2017"),
                         ("Date", "2018"),
                         ("Date", "1988"),
                         ("CLC", "all"), ]
    metadatas_protos = [("copyable", "true"),
                        ("disclaimer", "© le momo"),
                        ("snappingConfig", '{"tolerance": 50}')]

    groups = [LayerGroup(name='layer_group_{}'.format(i)) for i in range(0, 5)]

    layers = []
    for i in range(0, 25):
        layer = LayerWMS(name='layer_wms_{}'.format(i))
        layer.public = 1 == i % 2
        layer.ogc_server = servers[i % 4]
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]

        if i % 10 != 1:
            layer.interfaces = [interfaces[i % 4], interfaces[(i + 2) % 4]]

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
                    ('interfaces', "Interfaces"),
                    ('dimensions', "Dimensions", 'false'),
                    ('parents_relation', "Parents", 'false'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        check_grid_headers(test_app, '/layers_wms/', expected)

    def test_left_menu(self, test_app):
        html = test_app.get("/layers_wms/", status=200).html
        main_menu = html.select_one('a[href="http://localhost/layers_wms/"]').getText()
        assert 'WMS Layers' == main_menu

    def test_grid_complex_column_val(self, test_app, layer_wms_test_data):
        json = test_app.post(
            "/layers_wms/grid.json",
            params={
                "current": 1,
                "rowCount": 10,
                "sort[name]": "asc"
            },
            status=200
        ).json
        row = json["rows"][0]

        layer = layer_wms_test_data['layers'][0]

        assert layer.id == int(row["_id_"])
        assert layer.name == row["name"]
        assert 'restrictionarea_0, restrictionarea_2' == row['restrictionareas']
        assert 'server_0' == row['ogc_server']
        assert 'desktop, edit' == row['interfaces']
        assert 'Date: 2017, 1988; CLC: all' == row['dimensions']
        assert 'layer_group_0, layer_group_3' == row['parents_relation']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == row['metadatas']

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

    def test_edit(self, test_app, layer_wms_test_data, dbsession):
        layer = layer_wms_test_data['layers'][0]

        resp = test_app.get('/layers_wms/{}'.format(layer.id), status=200)
        form = resp.form

        assert str(layer.id) == form['id'].value
        assert 'hidden' == form['id'].attrs['type']
        assert layer.name == form['name'].value
        assert str(layer.metadata_url or '') == form['metadata_url'].value
        assert str(layer.description or '') == form['description'].value
        assert layer.public is False
        assert layer.public == form['public'].checked
        assert str(layer.geo_table or '') == form['geo_table'].value
        assert str(layer.exclude_properties or '') == form['exclude_properties'].value
        assert str(layer.ogc_server_id) == form['ogc_server_id'].value
        assert str(layer.layer or '') == form['layer'].value
        assert str(layer.style or '') == form['style'].value
        assert str(layer.time_mode) == form['time_mode'].value
        assert str(layer.time_widget) == form['time_widget'].value

        # interfaces
        interfaces = layer_wms_test_data['interfaces']
        assert [interfaces[0].id, interfaces[2].id] == [interface.id for interface in layer.interfaces]
        for i, interface in enumerate(sorted(interfaces, key=lambda ra: ra.name)):
            field = form.get('interfaces', index=i)
            checkbox = form.html.select_one("#{}".format(field.id))
            label = form.html.select_one("label[for={}]".format(field.id))
            assert interface.name == list(label.stripped_strings)[0]
            assert str(interface.id) == checkbox['value']
            assert (interface in layer.interfaces) == field.checked

        # restrictionareas
        ras = layer_wms_test_data['restrictionareas']
        assert [ras[0].id, ras[2].id] == [ra.id for ra in layer.restrictionareas]
        for i, ra in enumerate(sorted(ras, key=lambda ra: ra.name)):
            field = form.get('restrictionareas', index=i)
            checkbox = form.html.select_one("#{}".format(field.id))
            label = form.html.select_one("label[for={}]".format(field.id))
            assert ra.name == list(label.stripped_strings)[0]
            assert str(ra.id) == checkbox['value']
            assert (ra in layer.restrictionareas) == field.checked

        new_values = {
            'name': 'new_name',
            'metadata_url': 'https://new_metadata_url',
            'description': 'new description',
            'public': True,
            'geo_table': 'new_geo_table',
            'exclude_properties': 'property1,property2',
            'ogc_server_id': '2',
            'layer': 'new_wmslayername',
            'style': 'new_style',
            'time_mode': 'range',
            'time_widget': 'datepicker',
        }
        for key, value in new_values.items():
            form[key] = value
        form['interfaces'] = [interfaces[1].id, interfaces[3].id]
        form['restrictionareas'] = [ras[1].id, ras[3].id]

        resp = form.submit("submit")
        assert str(layer.id) == re.match('http://localhost/layers_wms/(.*)', resp.location).group(1)

        dbsession.expire(layer)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(layer, key)
            else:
                assert str(value or '') == str(getattr(layer, key) or '')
        assert set([interfaces[1].id, interfaces[3].id]) == set(
            [interface.id for interface in layer.interfaces])
        assert set([ras[1].id, ras[3].id]) == set([ra.id for ra in layer.restrictionareas])

    def test_grid_filter_on_interfaces(self, test_app):
        json = test_app.post(
            '/layers_wms/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'mobile'
            },
            status=200
        ).json
        assert 9 == json['total']

    def test_grid_filter_on_interfaces_blank_does_not_discard_anything(self, test_app):
        json = test_app.post(
            '/layers_wms/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': ''
            },
            status=200
        ).json
        assert 25 == json['total']

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS, Layer, TreeItem
        layer_id = dbsession.query(LayerWMS.id).first().id

        test_app.delete("/layers_wms/{}".format(layer_id), status=200)

        assert dbsession.query(LayerWMS).get(layer_id) is None
        assert dbsession.query(Layer).get(layer_id) is None
        assert dbsession.query(TreeItem).get(layer_id) is None

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
