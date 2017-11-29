# pylint: disable=no-self-use

import pytest

from . import check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def insert_layer_wmts_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMTS, RestrictionArea

    dbsession.begin_nested()
    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name='restrictionarea_{}'.format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    for i in range(0, 25):
        name = 'layer_wmts_{}'.format(i)
        layer = LayerWMTS(name=name)
        layer.layer = name
        layer.url = 'https://server{}.net/wmts'.format(i)
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]
        dbsession.add(layer)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures('insert_layer_wmts_test_data', 'transact', 'test_app')
class TestLayerWMTS():

    def test_view_index_rendering_in_app(self, test_app):
        expected = [('_id_', ''),
                    ('name', 'Name'),
                    ('public', 'Public'),
                    ('layer', 'WMTS layer name')]
        check_grid_headers(test_app, '/layers_wmts/', expected)

    def test_grid_complex_column_val(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import LayerWMTS
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
        layer = dbsession.query(LayerWMTS). \
            filter(LayerWMTS.id == row['_id_']). \
            one_or_none()
        assert layer.id == int(row['_id_'])
        assert layer.name == row['name']

    def test_left_menu(self, test_app):
        html = test_app.get('/layers_wmts/', status=200).html
        main_menu = html.select_one('a[href="http://localhost/layers_wmts/"]').getText()
        assert 'WMTS Layers' == main_menu
