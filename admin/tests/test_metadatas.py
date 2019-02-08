# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests, skip_if_ci
from .selenium.page import IndexPage


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession', 'transact')
def metadatas_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import \
        LayerWMS, LayerWMTS, LayerV1, OGCServer, Metadata, Theme, LayerGroup

    ogc_server = OGCServer(name='ogc_server')

    layer_wms = LayerWMS(name='layer_wms')
    layer_wms.layer = 'wms_layer'
    layer_wms.ogc_server = ogc_server
    layer_wms.metadatas = [
        Metadata(name, value)
        for name, value in [
            ('_string', 'ceci est un test'),
            ('_liste', 'valeur1,valeur2'),
            ('_boolean', 'true'),
            ('_int', '1'),
            ('_float', '2.5'),
            ('_url', 'https://localhost/test.html'),
            ('_json', '{"key":"value"}'),
            ('_color', '#FFFFFF'),
            ('_unknown', 'This is a unknown format')
        ]
    ]
    for metadata in layer_wms.metadatas:
        metadata.item = layer_wms
    dbsession.add(layer_wms)

    layer_wmts = LayerWMTS(name='layer_wmts')
    layer_wmts.url = 'https://localhost'
    layer_wmts.layer = 'wmts_layer'
    dbsession.add(layer_wmts)

    layer_v1 = LayerV1(name='layer_v1')
    dbsession.add(layer_v1)

    theme = Theme(name='theme')
    dbsession.add(theme)

    group = LayerGroup(name='groups')
    dbsession.add(group)

    dbsession.flush()

    yield {
        'ogc_server': ogc_server,
        'layer_wms': layer_wms,
        'layer_wmts': layer_wmts,
        'layer_v1': layer_v1,
        'theme': theme,
        'group': group
    }


@pytest.mark.usefixtures('metadatas_test_data', 'test_app')
class TestMetadatasView(AbstractViewsTests):

    _prefix = '/'

    def __metadata_ui_types(self):
        return ('string', 'liste', 'boolean', 'int', 'float', 'url', 'json')

    def __metadata_ui_type(self, test_app, name):
        settings = test_app.app.registry.settings
        return next(
            (
                m.get('type', 'string')
                for m in settings['admin_interface']['available_metadata']
                if m['name'] == name and m['type'] in self.__metadata_ui_types()
            ),
            'string')

    def _check_metadatas(self, test_app, item, metadatas):
        settings = test_app.app.registry.settings
        self._check_sequence(item, [
            [
                {
                    'name': 'id',
                    'value': str(m.id),
                    'hidden': True
                },
                {
                    'name': 'name',
                    'value': [
                        {
                            'text': s_m['name'],
                            'value': s_m['name'],
                            'selected': s_m['name'] == m.name
                        }
                        for s_m in sorted(settings['admin_interface']['available_metadata'],
                                          key=lambda m: m['name'])
                    ],
                    'label': 'Name',
                },
                {
                    'name': self.__metadata_ui_type(test_app, m.name),
                    'value': m.value,
                },
                {
                    'name': 'description',
                    'value': m.description,
                    'label': 'Description'
                }
            ]
            for m in metadatas]
        )

    def _post_metadata(self, test_app, url, base_mapping, name, value, status):
        return test_app.post(
            url,
            base_mapping + (
                ('__start__', 'metadatas:sequence'),
                ('__start__', 'metadata:mapping'),
                ('name', name),
                (self.__metadata_ui_type(test_app, name), value),
                ('__end__', 'metadata:mapping'),
                ('__end__', 'metadatas:sequence'),
            ),
            status=status)

    def _post_invalid_metadata(self, test_app, url, base_mapping, name, value, error_msg):
        resp = self._post_metadata(
            test_app, url, base_mapping, name, value, 200
        )
        assert error_msg == \
            resp.html.select_one(
                '.item-{} .help-block'.format(self.__metadata_ui_type(test_app, name))
            ).getText().strip()
        return resp

    @staticmethod
    def _base_metadata_params(metadatas_test_data):
        return (
            ('name', 'new_name'),
            ('ogc_server_id', metadatas_test_data['ogc_server'].id),
            ('layer', 'new_wmslayername')
        )

    def test_invalid_float_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_float',
            'number',
            '"number" is not a number')

    def test_valid_float_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_float',
            '2.5',
            302)

    def test_invalid_int_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_int',
            'number',
            '"number" is not a number')

    def test_valid_int_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_int',
            '2',
            302)

    def test_invalid_url_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_url',
            'gnagnagna',
            'Must be a URL')

    def test_valid_url_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_url',
            'www.111111111111111111111111111111111111111111111111111111111111.com',
            302)

    def test_invalid_json_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_json',
            '''{"colors": [{
                "color": "black",
                "category": "hue",
                "type": "primary",
                "code": {
                    "rgba": [255,255,255,1,
                    "hex": "#000"
                }
            }]}''',
            'Parser report: "Expecting \',\' delimiter: line 7 column 26 (char 213)"')

    def test_valid_json_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_json',
            '''{"colors": [{
                "color": "black",
                "category": "hue",
                "type": "primary",
                "code": {
                    "rgba": [255,255,255,1],
                    "hex": "#000"
                }
            }]}''',
            302)

    def test_invalid_color(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_color',
            '#W007DCD',
            'Expecting hex format for color, e.g. #007DCD')

    def test_valid_color(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            '/layers_wms/new',
            self._base_metadata_params(metadatas_test_data),
            '_color',
            '#007DCD',
            302)

    def _test_edit_treeitem(self, prefix, item, test_app):
        resp = self.get(test_app, '{}/{}'.format(prefix, item.id))
        self._check_metadatas(test_app,
                              resp.html.select_one('.item-metadatas'),
                              item.metadatas)
        resp.form.submit('submit', status=302)

    def test_layer_wms_metadatas(self, metadatas_test_data, test_app):
        self._test_edit_treeitem('layers_wms', metadatas_test_data['layer_wms'], test_app)

    def test_layer_wmts_metadatas(self, metadatas_test_data, test_app):
        self._test_edit_treeitem('layers_wmts', metadatas_test_data['layer_wmts'], test_app)

    def test_layer_v1_metadatas(self, metadatas_test_data, test_app):
        self._test_edit_treeitem('layers_v1', metadatas_test_data['layer_v1'], test_app)

    def test_theme_metadatas(self, metadatas_test_data, test_app):
        self._test_edit_treeitem('themes', metadatas_test_data['theme'], test_app)

    def test_group_metadatas(self, metadatas_test_data, test_app):
        self._test_edit_treeitem('layer_groups', metadatas_test_data['group'], test_app)


@skip_if_ci
@pytest.mark.selenium
@pytest.mark.usefixtures('selenium', 'selenium_app', 'metadatas_test_data')
class TestMetadatasSelenium():

    def test_hidden_type_validator_does_not_take_precedence_over_visible(
            self, selenium, selenium_app, metadatas_test_data):
        layer = metadatas_test_data['layer_wms']
        selenium.get(selenium_app + '/layers_wms/{}'.format(layer.id))
        selenium.execute_script("window.scrollBy(0,3000)", "")
        selenium.find_element_by_xpath(
            '''//div[contains(., "Metadatas")]
            /following-sibling::div[@class="panel-footer"]/a[@href="#"]''').click()
        selenium.execute_script("window.scrollBy(0,3000)", "")
        selenium.find_elements_by_xpath(
            '''//div[contains(., "Metadatas")]//label[contains(., "Name")]
            /following-sibling::select/option[contains(.,"_int")]''')[9].click()
        selenium.find_elements_by_xpath(
            '//div[contains(., "Metadatas")]//input[@name="int"]')[9].send_keys('AAA')

        selenium.find_element_by_id('deformformsubmit').click()

        assert '"AAA" is not a number' == selenium.find_element_by_xpath('//p[@class="help-block"]').text

        selenium.find_elements_by_xpath(
            '''//div[contains(., "Metadatas")]//label[contains(., "Name")]
            /following-sibling::select/option[contains(.,"_color")]''')[9].click()
        selenium.find_elements_by_xpath(
            '//div[contains(., "Metadatas")]//input[@name="string"]')[9].send_keys('BBB')

        selenium.find_element_by_id('deformformsubmit').click()

        assert 'Expecting hex format for color, e.g. #007DCD' == \
            selenium.find_element_by_xpath('//p[@class="help-block"]').text

        # have to check there are no side effects, especially that modifications held at template side
        # don't trigger "are you sure you want to leave alert"
        layer = metadatas_test_data['layer_wms']
        IndexPage(selenium)
        selenium.get(selenium_app + '/layers_wms/{}'.format(layer.id))

        selenium.find_element_by_xpath('//a[contains(@href, "roles")]').click()
        assert selenium.current_url.endswith('/roles')
