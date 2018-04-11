# pylint: disable=no-self-use

import re
import pytest

from . import skip_if_ci, AbstractViewsTests, factory_build_layers
from .selenium.page import IndexPage


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession', 'transact')
def layer_v1_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerV1

    def layer_builder(i):
        layer = LayerV1(name='layer_v1_{}'.format(i))
        layer.public = 1 == i % 2
        layer.image_type = 'image/jpeg'
        return layer

    datas = factory_build_layers(layer_builder, dbsession, add_dimension=False)

    dbsession.flush()

    yield datas


@pytest.mark.usefixtures('layer_v1_test_data', 'test_app')
class TestLayerV1Views(AbstractViewsTests):

    _prefix = '/layers_v1'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'Layers V1')

        expected = [('actions', '', 'false'),
                    ('id', 'id', 'true'),
                    ('name', 'Name'),
                    ('metadata_url', 'Metadata URL'),
                    ('description', 'Description'),
                    ('public', 'Public'),
                    ('geo_table', 'Geo table'),
                    ('exclude_properties', 'Exclude properties'),
                    ('layer', 'Layer name'),
                    ('is_checked', 'Is checked'),
                    ('icon', 'Icon'),
                    ('layer_type', 'Layer type'),
                    ('url', 'URL'),
                    ('image_type', 'Image type'),
                    ('style', 'Style'),
                    ('dimensions', 'Dimensions'),
                    ('matrix_set', 'Matrix set'),
                    ('wms_url', 'WMS URL'),
                    ('wms_layers', 'WMS layers'),
                    ('query_layers', 'Query layers'),
                    ('kml', 'KML'),
                    ('is_single_tile', 'Is single tile'),
                    ('legend', 'Legend'),
                    ('legend_image', 'Legend image'),
                    ('legend_rule', 'Legend rule'),
                    ('is_legend_expanded', 'Is legend expanded'),
                    ('min_resolution', 'Min resolution'),
                    ('max_resolution', 'Max resolution'),
                    ('disclaimer', 'Disclaimer'),
                    ('identifier_attribute_field', 'Identifier field'),
                    ('time_mode', 'Time mode'),
                    ('time_widget', 'Time widget'),
                    ('interfaces', 'Interfaces'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('parents_relation', 'Parents', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_v1_test_data):
        json = self.check_search(test_app, sort='name', total=25)

        row = json['rows'][0]
        layer = layer_v1_test_data['layers'][0]

        assert layer.id == int(row['_id_'])
        assert layer.name == row['name']
        assert 'restrictionarea_0, restrictionarea_2' == row['restrictionareas']
        assert 'desktop, edit' == row['interfaces']
        assert 'layer_group_0, layer_group_3' == row['parents_relation']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == row['metadatas']
        assert 'image/jpeg' == row['image_type']

    def test_grid_search(self, test_app):
        # check search on interfaces
        self.check_search(test_app, 'mobile', total=9)

    def test_base_edit(self, test_app, layer_v1_test_data):
        layer = layer_v1_test_data['layers'][10]

        form = self.get_item(test_app, layer.id).form

        assert 'layer_v1_10' == self.get_first_field_named(form, 'name').value
        assert '' == self.get_first_field_named(form, 'description').value

    def test_public_checkbox_edit(self, test_app, layer_v1_test_data):
        layer = layer_v1_test_data['layers'][10]
        form = self.get_item(test_app, layer.id).form
        assert not form['public'].checked

        layer = layer_v1_test_data['layers'][11]
        form = self.get_item(test_app, layer.id).form
        assert form['public'].checked

    def test_edit(self, test_app, layer_v1_test_data, dbsession):
        layer = layer_v1_test_data['layers'][0]

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
        assert str(layer.layer or '') == form['layer'].value
        assert str(layer.style or '') == form['style'].value
        assert str(layer.time_mode) == form['time_mode'].value
        assert str(layer.time_widget) == form['time_widget'].value

        interfaces = layer_v1_test_data['interfaces']
        assert set((interfaces[0].id, interfaces[2].id)) == set(i.id for i in layer.interfaces)
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in layer.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

        ras = layer_v1_test_data['restrictionareas']
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
            'layer': 'new_layername',
            'style': 'new_style',
            'time_mode': 'range',
            'time_widget': 'datepicker',
            'image_type': ''
        }

        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)
        form['interfaces'] = [interfaces[1].id, interfaces[3].id]
        form['restrictionareas'] = [ras[1].id, ras[3].id]

        resp = form.submit('submit')
        assert str(layer.id) == re.match(
            'http://localhost/layers_v1/(.*)\?msg_col=submit_ok',
            resp.location).group(1)

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
        from c2cgeoportal_commons.models.main import LayerV1

        resp = test_app.post(
            '/layers_v1/new',
            {
                'name': 'new_name',
                'metadata_url': 'https://new_metadata_url',
                'description': 'new description',
                'public': True,
                'geo_table': 'new_geo_table',
                'exclude_properties': 'property1,property2',
                'layer': 'new_wmslayername',
                'style': 'new_style',
                'time_mode': 'range',
                'time_widget': 'datepicker',
            },
            status=302)

        layer = dbsession.query(LayerV1). \
            filter(LayerV1.name == 'new_name'). \
            one()
        assert str(layer.id) == re.match(
            'http://localhost/layers_v1/(.*)\?msg_col=submit_ok',
            resp.location).group(1)

    def test_duplicate(self, layer_v1_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerV1
        layer = layer_v1_test_data['layers'][3]

        resp = test_app.get("/layers_v1/{}/duplicate".format(layer.id), status=200)
        form = resp.form

        assert '' == self.get_first_field_named(form, 'id').value
        assert layer.name == self.get_first_field_named(form, 'name').value
        assert str(layer.metadata_url or '') == form['metadata_url'].value
        assert str(layer.description or '') == self.get_first_field_named(form, 'description').value
        assert layer.public is True
        assert layer.public == form['public'].checked
        assert str(layer.geo_table or '') == form['geo_table'].value
        assert str(layer.exclude_properties or '') == form['exclude_properties'].value
        assert str(layer.layer or '') == form['layer'].value
        assert str(layer.style or '') == form['style'].value
        assert str(layer.time_mode) == form['time_mode'].value
        assert str(layer.time_widget) == form['time_widget'].value
        interfaces = layer_v1_test_data['interfaces']
        assert set((interfaces[3].id, interfaces[1].id)) == set(i.id for i in layer.interfaces)
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in layer.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

        ras = layer_v1_test_data['restrictionareas']
        assert set((ras[3].id, ras[0].id)) == set(i.id for i in layer.restrictionareas)
        self.check_checkboxes(
            form,
            'restrictionareas',
            [{
                'label': ra.name,
                'value': str(ra.id),
                'checked': ra in layer.restrictionareas
            } for ra in sorted(ras, key=lambda ra: ra.name)])

        self.set_first_field_named(form, 'name', 'clone')
        resp = form.submit('submit')

        layer = dbsession.query(LayerV1). \
            filter(LayerV1.name == 'clone'). \
            one()
        assert str(layer.id) == re.match(
            'http://localhost/layers_v1/(.*)\?msg_col=submit_ok',
            resp.location).group(1)
        assert layer_v1_test_data['layers'][3].metadatas[0].name == layer.metadatas[0].name
        assert layer_v1_test_data['layers'][3].metadatas[1].name == layer.metadatas[1].name

    def test_unicity_validator(self, layer_v1_test_data, test_app):
        layer = layer_v1_test_data['layers'][2]
        resp = test_app.get("/layers_v1/{}/duplicate".format(layer.id), status=200)

        resp = resp.form.submit('submit')

        self._check_submission_problem(resp, '{} is already used.'.format(layer.name))

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerV1, Layer, TreeItem
        layer_id = dbsession.query(LayerV1.id).first().id

        test_app.delete('/layers_v1/{}'.format(layer_id), status=200)

        assert dbsession.query(LayerV1).get(layer_id) is None
        assert dbsession.query(Layer).get(layer_id) is None
        assert dbsession.query(TreeItem).get(layer_id) is None


@skip_if_ci
@pytest.mark.selenium
@pytest.mark.usefixtures('selenium', 'selenium_app', 'layer_v1_test_data')
class TestLayerV1Selenium():

    _prefix = '/layers_v1'

    def test_index(self, selenium, selenium_app):
        selenium.get(selenium_app + self._prefix)

        index_page = IndexPage(selenium)
        index_page.select_language('en')
        index_page.check_pagination_info('Showing 1 to 25 of 25 rows', 10)
        index_page.select_page_size(10)
        index_page.check_pagination_info('Showing 1 to 10 of 25 rows', 10)
