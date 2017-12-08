# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def layer_wmts_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMTS, RestrictionArea

    dbsession.begin_nested()

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name='restrictionarea_{}'.format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    layers = []
    for i in range(0, 25):
        name = 'layer_wmts_{}'.format(i)
        layer = LayerWMTS(name=name)
        layer.layer = name
        layer.url = 'https://server{}.net/wmts'.format(i)
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]
        dbsession.add(layer)
        layers.append(layer)

    yield {
        'layers': layers
    }

    dbsession.rollback()


@pytest.mark.usefixtures('layer_wmts_test_data', 'transact', 'test_app')
class TestLayerWMTS(AbstractViewsTests):

    _prefix = '/layers_wmts'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'WMTS Layers')

        expected = [('_id_', '', 'false'),
                    ('name', 'Name', 'true'),
                    ('metadata_url', 'Metadata URL', 'true'),
                    ('description', 'Description', 'true'),
                    ('public', 'Public', 'true'),
                    ('geo_table', 'Geo table', 'true'),
                    ('exclude_properties', 'Exclude properties', 'true'),
                    ('url', 'GetCapabilities URL', 'true'),
                    ('layer', 'WMTS layer name', 'true'),
                    ('style', 'Style', 'true'),
                    ('matrix_set', 'Matrix set', 'true'),
                    ('image_type', 'Image type', 'true'),
                    ('dimensions', 'Dimensions', 'false'),
                    ('parents_relation', 'Parents', 'false'),
                    ('interfaces', 'Interfaces', 'true'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_wmts_test_data):
        json = test_app.post(
            '/layers_wmts/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'sort[name]': 'asc'
            },
            status=200
        ).json
        row = json['rows'][0]

        layer = layer_wmts_test_data['layers'][0]

        assert layer.id == int(row['_id_'])
        assert layer.name == row['name']
