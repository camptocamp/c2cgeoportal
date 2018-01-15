# pylint: disable=no-self-use

import pytest

from . import skip_if_ci, AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def layertree_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerGroup, LayergroupTreeitem, LayerV1, LayerWMS, LayerWMTS, OGCServer, Theme

    dbsession.begin_nested()

    layers_v1 = []
    for i in range(0, 10):
        layer_v1 = LayerV1(name='layer_v1_{}'.format(i))
        layers_v1.append(layer_v1)
        dbsession.add(layer_v1)

    layers_wms = []
    ogc_server = OGCServer(name='ogc_server')
    dbsession.add(ogc_server)
    for i in range(0, 10):
        layer_wms = LayerWMS(name='layer_wms_{}'.format(i))
        layer_wms.ogc_server = ogc_server
        layers_wms.append(layer_wms)
        dbsession.add(layer_wms)

    layers_wmts = []
    for i in range(0, 10):
        layer_wmts = LayerWMTS(name='layer_wmts_{}'.format(i))
        layer_wmts.url = 'http://localhost/wmts'
        layer_wmts.layer = layer_wmts.name
        layers_wmts.append(layer_wmts)
        dbsession.add(layer_wmts)

    groups = []
    for i in range(0, 10):
        group = LayerGroup(name='layer_group_{}'.format(i))
        groups.append(group)
        dbsession.add(group)

        for j, items in enumerate((layers_v1, layers_wms, layers_wmts)):
            dbsession.add(LayergroupTreeitem(group=group, item=items[i], ordering=j))

    # a group in a group
    dbsession.add(LayergroupTreeitem(group=groups[9], item=groups[8], ordering=3))

    themes = []
    for i in range(0, 5):
        theme = Theme(name='theme_{}'.format(i))
        themes.append(theme)
        dbsession.add(theme)

        dbsession.add(LayergroupTreeitem(group=theme, item=groups[i], ordering=0))
        dbsession.add(LayergroupTreeitem(group=theme, item=groups[i + 5], ordering=1))

    themes[0].ordering = 1
    themes[3].ordering = 2
    themes[1].ordering = 3
    themes[2].ordering = 4
    themes[4].ordering = 5

    dbsession.flush()

    yield({
        'themes': themes,
        'groups': groups,
        'layers_v1': layers_v1,
        'layers_wms': layers_wms,
        'layers_wmts': layers_wmts,
    })

    dbsession.rollback()


@pytest.mark.usefixtures('dbsession', 'layertree_test_data', 'transact', 'test_app')
class TestLayerTreeView(AbstractViewsTests):

    _prefix = '/layertree'

    def test_index_rendering(self, test_app, layertree_test_data):
        html = self.get(test_app).html

        # check themes are sorted by ordering
        theme_names = [list(tr.select('td')[0].stripped_strings)[0]
                       for tr in html.select('tr.theme')]
        expected = [theme.name for theme in sorted(layertree_test_data['themes'],
                                                   key=lambda theme: theme.ordering)]
        assert expected == theme_names

        # check total number of nodes
        lines = html.select('#layertree-table tr')
        nb_themes = 5
        nb_groups = 10 + 1  # group 1 in group 9
        nb_layers = nb_groups * 3
        assert nb_themes + nb_groups + nb_layers == len(lines)

    def test_edit_button(self, test_app, layertree_test_data):
        resp = self.get(test_app)

        for table, item_id in (
            ('themes', layertree_test_data['themes'][0].id),
            ('layer_groups', layertree_test_data['groups'][0].id),
            ('layers_v1', layertree_test_data['layers_v1'][0].id),
            ('layers_wms', layertree_test_data['layers_wms'][0].id),
            ('layers_wmts', layertree_test_data['layers_wmts'][0].id),
        ):
            link = resp.html.select_one('tr.treegrid-{} li.action-edit a'.format(item_id))
            assert 'http://localhost/{}/{}'.format(table, item_id) == link['href']
            test_app.get(link['href'], status=200)

    def test_unlink_button(self, test_app, layertree_test_data):
        resp = self.get(test_app)

        # no unlink on theme
        assert 0 == len(
            resp.html.select('tr.treegrid-{} li.action-unlink a'
                             .format(layertree_test_data['themes'][0].id)))

        for group_id, item_id in (
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_wmts'][0].id),
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_wms'][0].id),
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_v1'][0].id),
            (layertree_test_data['themes'][0].id, layertree_test_data['groups'][0].id),
        ):
            link = resp.html.select_one('tr.treegrid-{}.treegrid-parent-{} li.action-unlink a'.
                                        format(item_id, group_id))
            assert 'http://localhost/layertree/unlink/{}/{}'.format(group_id, item_id) == link['data-url']

    def test_unlink_view(self, test_app, layertree_test_data, dbsession):
        group = layertree_test_data['groups'][0]
        item = layertree_test_data['layers_wms'][0]

        test_app.delete('/layertree/unlink/{}/{}'.format(group.id, item.id), status=200)

        dbsession.expire_all()

        assert item not in group.children

    @skip_if_ci
    @pytest.mark.selenium
    @pytest.mark.usefixtures('selenium', 'selenium_app')
    def test_unlink_selenium(self, dbsession, selenium, selenium_app, layertree_test_data):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions
        from selenium.webdriver.support.ui import WebDriverWait

        selenium.get(selenium_app + self._prefix)

        elem = WebDriverWait(selenium, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, 'layertree-expand')))
        elem.click()

        for group_id, item_id in (
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_wmts'][0].id),
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_wms'][0].id),
            (layertree_test_data['groups'][0].id, layertree_test_data['layers_v1'][0].id),
            (layertree_test_data['themes'][0].id, layertree_test_data['groups'][0].id),
        ):
            elem = WebDriverWait(selenium, 10).until(
                expected_conditions.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'tr.treegrid-{}.treegrid-parent-{} button.dropdown-toggle'.
                    format(item_id, group_id)
                ))
            )
            elem.click()

            elem = WebDriverWait(selenium, 10).until(
                expected_conditions.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'tr.treegrid-{}.treegrid-parent-{} li.action-unlink a'.
                    format(item_id, group_id)
                ))
            )
            expected_url = '{}/layertree/unlink/{}/{}'.format(selenium_app, group_id, item_id)
            assert expected_url == elem.get_attribute('data-url')

            elem.click()
            selenium.switch_to_alert().accept()
            selenium.switch_to_default_content()

            WebDriverWait(selenium, 10).until(
                lambda driver: driver.execute_script(
                    'return (window.jQuery != undefined && jQuery.active == 0)'))

            from c2cgeoportal_commons.models.main import LayergroupTreeitem
            link = dbsession.query(LayergroupTreeitem). \
                filter(LayergroupTreeitem.treegroup_id == group_id). \
                filter(LayergroupTreeitem.treeitem_id == item_id). \
                one_or_none()
            assert link is None

            dbsession.expire_all()
            selenium.refresh()

            from selenium.common.exceptions import NoSuchElementException
            with pytest.raises(NoSuchElementException):
                elem = selenium.find_element_by_css_selector('tr.treegrid-{}.treegrid-parent-{}'
                                                             .format(item_id, group_id))
