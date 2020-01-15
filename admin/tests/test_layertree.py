# pylint: disable=no-self-use

from unittest.mock import patch

import pytest
from selenium.common.exceptions import NoSuchElementException

from . import AbstractViewsTests, skip_if_ci
from .selenium.page import LayertreePage


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def layertree_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import (
        LayerGroup,
        LayergroupTreeitem,
        LayerWMS,
        LayerWMTS,
        OGCServer,
        Theme,
    )

    layers_wms = []
    ogc_server = OGCServer(name="ogc_server")
    dbsession.add(ogc_server)
    for i in range(0, 10):
        layer_wms = LayerWMS(name="layer_wms_{}".format(i))
        layer_wms.ogc_server = ogc_server
        layers_wms.append(layer_wms)
        dbsession.add(layer_wms)

    layers_wmts = []
    for i in range(0, 10):
        layer_wmts = LayerWMTS(name="layer_wmts_{}".format(i))
        layer_wmts.url = "http://localhost/wmts"
        layer_wmts.layer = layer_wmts.name
        layers_wmts.append(layer_wmts)
        dbsession.add(layer_wmts)

    groups = []
    for i in range(0, 10):
        group = LayerGroup(name="layer_group_{}".format(i))
        groups.append(group)
        dbsession.add(group)

        for j, items in enumerate((layers_wms, layers_wmts)):
            dbsession.add(LayergroupTreeitem(group=group, item=items[i], ordering=j))

    # a group in a group
    dbsession.add(LayergroupTreeitem(group=groups[9], item=groups[8], ordering=3))

    themes = []
    for i in range(0, 5):
        theme = Theme(name="theme_{}".format(i))
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

    yield (
        {
            "themes": themes,
            "groups": groups,
            "layers_wms": layers_wms,
            "layers_wmts": layers_wmts,
            "ogc_servers": [ogc_server],
        }
    )


@patch(
    "c2cgeoportal_admin.views.layertree.TranslationStringFactory",
    new=lambda factory_domain: (str(factory_domain) + "_{}_").format,
)
@pytest.mark.usefixtures("layertree_test_data", "test_app")
class TestLayerTreeView(AbstractViewsTests):

    _prefix = "/admin/layertree"

    def test_index(self, test_app):
        self.get(test_app, status=200)

    def check_edit_action(self, test_app, nodes, table, item_id):
        node = next(n for n in nodes if n["id"] == item_id)
        action = next(a for a in node["actions"] if a["name"] == "edit")
        assert "http://localhost/admin/{}/{}".format(table, item_id) == action["url"]
        test_app.get(action["url"], status=200)

    def check_unlink_action(self, test_app, nodes, group_id, item_id):
        node = next(n for n in nodes if n["id"] == item_id)
        action = next(a for a in node["actions"] if a["name"] == "unlink")
        assert "http://localhost/admin/layertree/unlink/{}/{}".format(group_id, item_id) == action["url"]
        test_app.delete(action["url"], status=200)

    def check_translation(self, nodes, item):
        node = next(n for n in nodes if n["id"] == item.id)
        expected_factory_domain = "c2cgeoportal_admin-client"
        assert (expected_factory_domain + "_{}_").format(item.name) == node["translated_name"]

    def check_new_action(self, test_app, nodes, parent_id, action_name, label, route_table, required_fields):
        node = next(n for n in nodes if n["id"] == parent_id)
        action = next(a for a in node["actions"] if a["name"] == action_name)
        assert label == action["label"]
        assert "http://localhost/admin/{}/new?parent_id={}".format(route_table, parent_id) == action["url"]

        form = test_app.get(action["url"], status=200).form
        assert form["parent_id"].value == str(parent_id)
        for required_field in required_fields:
            form[required_field] = required_fields[required_field]
        form.submit("submit", 302)

    def test_themes(self, test_app, layertree_test_data):
        resp = self.get(test_app, "/children", status=200)
        nodes = resp.json
        assert 5 == len(nodes)

        # check themes are sorted by ordering
        expected = [
            theme.name for theme in sorted(layertree_test_data["themes"], key=lambda theme: theme.ordering)
        ]
        theme_names = [node["name"] for node in nodes if node["item_type"] == "theme"]
        assert expected == theme_names

        theme = layertree_test_data["themes"][0]
        self.check_edit_action(test_app, nodes, "themes", theme.id)

        # no unlink on theme
        theme_node = next(n for n in nodes if n["id"] == theme.id)
        assert 0 == len([a for a in theme_node["actions"] if a["name"] == "unlink"])

        self.check_translation(nodes, theme)

        self.check_new_action(
            test_app,
            nodes,
            theme.id,
            "new_layer_group",
            "New layer group",
            "layer_groups",
            {"name": "new_name_from_layer_group"},
        )

    def test_groups(self, test_app, layertree_test_data):
        theme = layertree_test_data["themes"][0]
        resp = self.get(test_app, "/children?group_id={0}&path=_{0}".format(theme.id), status=200)
        nodes = resp.json
        assert 2 == len(nodes)

        group = layertree_test_data["groups"][0]
        self.check_edit_action(test_app, nodes, "layer_groups", group.id)
        self.check_unlink_action(test_app, nodes, theme.id, group.id)
        self.check_translation(nodes, group)

        ogc_server = layertree_test_data["ogc_servers"][0]
        self.check_new_action(
            test_app,
            nodes,
            group.id,
            "new_layer_wms",
            "New WMS layer",
            "layers_wms",
            {"ogc_server_id": ogc_server.id, "name": "layer-wms-from-tree", "layer": "layer-wms-from-tree"},
        )
        self.check_new_action(
            test_app,
            nodes,
            group.id,
            "new_layer_wmts",
            "New WMTS layer",
            "layers_wmts",
            {
                "url": "http://localhost/wmts/fromtree",
                "name": "layer-wmts-from-tree",
                "image_type": "image/jpeg",
                "layer": "layer-wmts-from-tree",
            },
        )

    def test_layers(self, test_app, layertree_test_data):
        theme = layertree_test_data["themes"][0]
        group = layertree_test_data["groups"][0]
        resp = self.get(
            test_app, "/children?group_id={0}&path=_{1}_{0}".format(group.id, theme.id), status=200
        )
        nodes = resp.json
        assert len(nodes) == 2

        layer_wms = layertree_test_data["layers_wms"][0]
        layer_wmts = layertree_test_data["layers_wmts"][0]

        for table, item_id in (("layers_wms", layer_wms.id), ("layers_wmts", layer_wmts.id)):
            self.check_edit_action(test_app, nodes, table, item_id)

        for group_id, item_id in ((group.id, layer_wmts.id), (group.id, layer_wms.id)):
            self.check_unlink_action(test_app, nodes, group_id, item_id)

        for item in [layer_wms, layer_wmts]:
            self.check_translation(nodes, item)

    def test_unlink(self, test_app, layertree_test_data, dbsession):
        group = layertree_test_data["groups"][0]
        item = layertree_test_data["layers_wms"][0]
        test_app.delete("/admin/layertree/unlink/{}/{}".format(group.id, item.id), status=200)
        dbsession.expire_all()
        assert item not in group.children


@skip_if_ci
@pytest.mark.selenium
@pytest.mark.usefixtures("selenium", "selenium_app", "layertree_test_data")
class TestLayerTreeSelenium:

    _prefix = "/layertree"

    def test_unlink(self, dbsession, selenium, selenium_app, layertree_test_data):
        from c2cgeoportal_commons.models.main import LayergroupTreeitem

        themes = layertree_test_data["themes"]
        groups = layertree_test_data["groups"]
        layers_wms = layertree_test_data["layers_wms"]
        layers_wmts = layertree_test_data["layers_wmts"]

        selenium.get(selenium_app + self._prefix)
        page = LayertreePage(selenium)
        page.expand()

        for group_id, item_id, path in (
            (
                groups[0].id,
                layers_wmts[0].id,
                "_{}_{}_{}".format(themes[0].id, groups[0].id, layers_wmts[0].id),
            ),
            (
                groups[0].id,
                layers_wms[0].id,
                "_{}_{}_{}".format(themes[0].id, groups[0].id, layers_wms[0].id),
            ),
            (themes[0].id, groups[0].id, "_{}_{}".format(themes[0].id, groups[0].id)),
        ):
            action_el = page.find_item_action(path, "unlink", 10)
            expected_url = "{}/layertree/unlink/{}/{}".format(selenium_app, group_id, item_id)
            assert expected_url == action_el.get_attribute("data-url")
            page.click_and_confirm(action_el)

            dbsession.expire_all()
            link = (
                dbsession.query(LayergroupTreeitem)
                .filter(LayergroupTreeitem.treegroup_id == group_id)
                .filter(LayergroupTreeitem.treeitem_id == item_id)
                .one_or_none()
            )
            assert link is None

            selenium.refresh()
            page.wait_jquery_to_be_active()
            page.find_item("_{}_{}_{}".format(themes[0].id, groups[5].id, layers_wmts[5].id), 10)
            with pytest.raises(NoSuchElementException):
                page.find_item(path)

    @skip_if_ci
    @pytest.mark.selenium
    @pytest.mark.usefixtures("selenium", "selenium_app")
    def test_delete(self, dbsession, selenium, selenium_app, layertree_test_data):
        from c2cgeoportal_commons.models.main import LayerWMS, LayerWMTS, LayerGroup

        themes = layertree_test_data["themes"]
        groups = layertree_test_data["groups"]
        layers_wms = layertree_test_data["layers_wms"]
        layers_wmts = layertree_test_data["layers_wmts"]

        selenium.get(selenium_app + self._prefix)
        page = LayertreePage(selenium)
        page.expand()

        for item_id, path, model in (
            (layers_wmts[1].id, "_{}_{}_{}".format(themes[1].id, groups[1].id, layers_wmts[1].id), LayerWMTS),
            (layers_wms[1].id, "_{}_{}_{}".format(themes[1].id, groups[1].id, layers_wms[1].id), LayerWMS),
            (groups[1].id, "_{}_{}".format(themes[1].id, groups[1].id), LayerGroup),
        ):
            action_el = page.find_item_action(path, "delete", 10)
            expected_url = "{}/admin/layertree/delete/{}".format(selenium_app, item_id)
            assert expected_url == action_el.get_attribute("data-url")
            page.click_and_confirm(action_el)
            page.wait_jquery_to_be_active()

            deleted = dbsession.query(model).filter(model.id == item_id).one_or_none()
            assert deleted is None

            dbsession.expire_all()
            selenium.refresh()
            page.wait_jquery_to_be_active()

            page.find_item("_{}_{}_{}".format(themes[1].id, groups[6].id, layers_wmts[6].id), 10)
            with pytest.raises(NoSuchElementException):
                page.find_item(path)
