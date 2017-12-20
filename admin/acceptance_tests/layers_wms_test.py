# pylint: disable=no-self-use

import re
import pytest

from . import skip_if_ci, AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def layer_wms_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMS, OGCServer, RestrictionArea, LayergroupTreeitem, \
        Interface, Dimension, Metadata, LayerGroup

    dbsession.begin_nested()

    servers = [OGCServer(name='server_{}'.format(i)) for i in range(0, 4)]

    restrictionareas = [RestrictionArea(name='restrictionarea_{}'.format(i))
                        for i in range(0, 5)]

    interfaces = [Interface(name) for name in ['desktop', 'mobile', 'edit', 'routing']]

    dimensions_protos = [('Date', '2017'),
                         ('Date', '2018'),
                         ('Date', '1988'),
                         ('CLC', 'all'), ]
    metadatas_protos = [('copyable', 'true'),
                        ('disclaimer', '© le momo'),
                        ('snappingConfig', '{"tolerance": 50}')]

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
        'servers': servers,
        'restrictionareas': restrictionareas,
        'layers': layers,
        'interfaces': interfaces
    }

    dbsession.rollback()


@pytest.mark.usefixtures('layer_wms_test_data', 'transact', 'test_app')
class TestLayerWMSViews(AbstractViewsTests):

    _prefix = '/layers_wms'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'WMS Layers')

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
                    ('dimensions', 'Dimensions', 'false'),
                    ('interfaces', 'Interfaces'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('parents_relation', 'Parents', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_wms_test_data):
        json = test_app.post(
            '/layers_wms/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'sort[name]': 'asc',
                'searchPhrase': ''
            },
            status=200
        ).json
        assert 25 == json['total']

        row = json['rows'][0]
        layer = layer_wms_test_data['layers'][0]

        assert layer.id == int(row['_id_'])
        assert layer.name == row['name']
        assert 'restrictionarea_0, restrictionarea_2' == row['restrictionareas']
        assert 'server_0' == row['ogc_server']
        assert 'desktop, edit' == row['interfaces']
        assert 'Date: 2017, 1988; CLC: all' == row['dimensions']
        assert 'layer_group_0, layer_group_3' == row['parents_relation']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == row['metadatas']

    def test_grid_sort_on_ogc_server(self, test_app, layer_wms_test_data):
        rows = test_app.post(
            '/layers_wms/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'sort[ogc_server]': 'asc'
            },
            status=200
        ).json['rows']
        for i, layer in enumerate(sorted(layer_wms_test_data['layers'],
                                         key=lambda layer: (layer.ogc_server.name, layer.id))):
            if i == 10:
                break
            assert str(layer.id) == rows[i]['_id_']

    def test_grid_search(self, test_app):
        # check search on ogc_server.name
        self.check_search(test_app, 'server_0', 7)

        # check search on interfaces
        self.check_search(test_app, 'mobile', 9)

    def test_base_edit(self, test_app, layer_wms_test_data):
        layer = layer_wms_test_data['layers'][10]

        form = self.get_item(test_app, layer.id).form

        assert 'layer_wms_10' == self.get_first_field_named(form, 'name').value
        assert '' == self.get_first_field_named(form, 'description').value

    def test_public_checkbox_edit(self, test_app, layer_wms_test_data):
        layer = layer_wms_test_data['layers'][10]
        form = self.get_item(test_app, layer.id).form
        assert not form['public'].checked

        layer = layer_wms_test_data['layers'][11]
        form = self.get_item(test_app, layer.id).form
        assert form['public'].checked

    def test_edit(self, test_app, layer_wms_test_data, dbsession):
        layer = layer_wms_test_data['layers'][0]

        form = self.get_item(test_app, layer.id).form

        assert str(layer.id) == self.get_first_field_named(form, 'id').value
        assert 'hidden' == self.get_first_field_named(form, 'id').attrs['type']
        assert layer.name == self.get_first_field_named(form, 'name').value
        assert str(layer.description or '') == self.get_first_field_named(form, 'description').value
        assert str(layer.metadata_url or '') == form['metadata_url'].value
        assert layer.public is False
        assert layer.public == form['public'].checked
        assert str(layer.geo_table or '') == form['geo_table'].value
        assert str(layer.exclude_properties or '') == form['exclude_properties'].value
        assert str(layer.ogc_server_id) == form['ogc_server_id'].value
        assert str(layer.layer or '') == form['layer'].value
        assert str(layer.style or '') == form['style'].value
        assert str(layer.time_mode) == form['time_mode'].value
        assert str(layer.time_widget) == form['time_widget'].value

        interfaces = layer_wms_test_data['interfaces']
        assert set((interfaces[0].id, interfaces[2].id)) == set(i.id for i in layer.interfaces)
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in layer.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

        ras = layer_wms_test_data['restrictionareas']
        assert set((ras[0].id, ras[2].id)) == set(i.id for i in layer.restrictionareas)
        self.check_checkboxes(
            form,
            'restrictionareas',
            [{
                'label': ra.name,
                'value': str(ra.id),
                'checked': ra in layer.restrictionareas
            } for ra in sorted(ras, key=lambda ra: ra.name)])

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
            self.set_first_field_named(form, key, value)
        form['interfaces'] = [interfaces[1].id, interfaces[3].id]
        form['restrictionareas'] = [ras[1].id, ras[3].id]

        resp = form.submit('submit')
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

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import LayerWMS

        resp = test_app.post(
            '/layers_wms/new',
            {
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
            },
            status=302)

        layer = dbsession.query(LayerWMS). \
            filter(LayerWMS.name == 'new_name'). \
            one()
        assert str(layer.id) == re.match('http://localhost/layers_wms/(.*)', resp.location).group(1)
        assert layer.name == 'new_name'

    def test_duplicate(self, layer_wms_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS
        layer = layer_wms_test_data['layers'][3]

        resp = test_app.get("/layers_wms/{}/duplicate".format(layer.id), status=200)
        form = resp.form

        assert '' == self.get_first_field_named(form, 'id').value
        assert layer.name == self.get_first_field_named(form, 'name').value
        assert str(layer.metadata_url or '') == form['metadata_url'].value
        assert str(layer.description or '') == self.get_first_field_named(form, 'description').value
        assert layer.public is True
        assert layer.public == form['public'].checked
        assert str(layer.geo_table or '') == form['geo_table'].value
        assert str(layer.exclude_properties or '') == form['exclude_properties'].value
        assert str(layer.ogc_server_id) == form['ogc_server_id'].value
        assert str(layer.layer or '') == form['layer'].value
        assert str(layer.style or '') == form['style'].value
        assert str(layer.time_mode) == form['time_mode'].value
        assert str(layer.time_widget) == form['time_widget'].value
        interfaces = layer_wms_test_data['interfaces']
        assert set((interfaces[3].id, interfaces[1].id)) == set(i.id for i in layer.interfaces)
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in layer.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

        ras = layer_wms_test_data['restrictionareas']
        assert set((ras[3].id, ras[0].id)) == set(i.id for i in layer.restrictionareas)
        self.check_checkboxes(
            form,
            'restrictionareas',
            [{
                'label': ra.name,
                'value': str(ra.id),
                'checked': ra in layer.restrictionareas
            } for ra in sorted(ras, key=lambda ra: ra.name)])

        assert '' == form.html.select(
            'input[value=dimensions:mapping] + input')[0].attrs['value']
        assert layer.dimensions[0].name == form.html.select(
            'input[value=dimensions:mapping] + input + div')[0].findChild('input').attrs['value']
        assert layer.dimensions[0].value == form.html.select(
            'input[value=dimensions:mapping] + input + div + div')[0].findChild('input').attrs['value']

        assert '' == form.html.select(
            'input[value=dimensions:mapping] + input')[2].attrs['value']
        assert layer.dimensions[2].name == form.html.select(
            'input[value=dimensions:mapping] + input + div')[2].findChild('input').attrs['value']
        assert layer.dimensions[2].value == form.html.select(
            'input[value=dimensions:mapping] + input + div + div')[2].findChild('input').attrs['value']

        self.set_first_field_named(form, 'name', 'clone')
        resp = form.submit('submit')

        layer = dbsession.query(LayerWMS). \
            filter(LayerWMS.name == 'clone'). \
            one()
        assert str(layer.id) == re.match('http://localhost/layers_wms/(.*)', resp.location).group(1)
        assert layer.id == layer.dimensions[0].layer_id
        assert layer.id == layer.metadatas[0].item_id
        assert layer_wms_test_data['layers'][3].metadatas[0].name == layer.metadatas[0].name
        assert layer_wms_test_data['layers'][3].metadatas[1].name == layer.metadatas[1].name

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS, Layer, TreeItem
        layer_id = dbsession.query(LayerWMS.id).first().id

        test_app.delete('/layers_wms/{}'.format(layer_id), status=200)

        assert dbsession.query(LayerWMS).get(layer_id) is None
        assert dbsession.query(Layer).get(layer_id) is None
        assert dbsession.query(TreeItem).get(layer_id) is None

    @pytest.mark.skip(reason='Contraint has to be added at model side, alambiced')
    def test_submit_new_no_layer_name(self, dbsession, test_app):
        resp = test_app.post(
            '/layers_wms/new',
            {
                'name': 'new_name',
                'metadata_url': 'https://new_metadata_url',
                'description': 'new description',
                'public': True,
                'geo_table': 'new_geo_table',
                'exclude_properties': 'property1,property2',
                'ogc_server_id': '2',
                'style': 'new_style',
                'time_mode': 'range',
                'time_widget': 'datepicker',
            },
            status=200)

        assert 'There was a problem with your submission' == \
            resp.html.select_one('div[class="error-msg-lbl"]').text
        assert 'Errors have been highlighted below' == \
            resp.html.select_one('div[class="error-msg-detail"]').text
        assert ['WMS layer name'] == \
            sorted([(x.select_one("label").text.strip())
                    for x in resp.html.select("[class~'has-error']")])

    @skip_if_ci
    @pytest.mark.selenium
    @pytest.mark.usefixtures('selenium', 'selenium_app')
    def test_selenium(self, selenium, selenium_app):
        selenium.get(selenium_app + self._prefix)

        elem = selenium.find_element_by_xpath('//a[contains(@href,"language=en")]')
        elem.click()

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions
        elem = WebDriverWait(selenium, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//div[@class="infos"]')))
        assert 'Showing 1 to 10 of 25 entries' == elem.text
        elem = selenium.find_element_by_xpath('//button[@title="Refresh"]/following-sibling::*')
        elem.click()
        elem = selenium.find_element_by_xpath('//a[contains(.,"50")]')
        elem.click()
