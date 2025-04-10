# pylint: disable=no-self-use

import re

import pytest

from . import AbstractViewsTests


@pytest.fixture
def edit_url_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import (
        Functionality,
        Interface,
        LayerGroup,
        LayerWMS,
        LayerWMTS,
        OGCServer,
        RestrictionArea,
        Role,
        Theme,
    )

    restrictionareas = [RestrictionArea(name=f"restrictionarea_{i}") for i in range(5)]
    functionalities = {}
    for name in ("default_basemap", "default_theme"):
        functionalities[name] = []
        for v in range(4):
            functionality = Functionality(name=name, value=f"value_{v}")
            dbsession.add(functionality)
            functionalities[name].append(functionality)

    interfaces = [Interface(name) for name in ["desktop", "mobile", "edit", "routing"]]
    ogc_server = OGCServer(name="ogc_server")

    layers_wmts = []
    for i in range(5):
        name = f"layer_wmts_{i}"
        layer_wmts = LayerWMTS(name=name)
        layer_wmts.layer = name
        layer_wmts.url = f"https://server{i}.net/wmts"
        layer_wmts.restrictionareas = [restrictionareas[i % 5], restrictionareas[(i + 2) % 5]]
        if i % 10 != 1:
            layer_wmts.interfaces = [interfaces[i % 4], interfaces[(i + 2) % 4]]
        layer_wmts.public = i % 2 == 1
        layer_wmts.image_type = "image/jpeg"
        dbsession.add(layer_wmts)
        layers_wmts.append(layer_wmts)

    layers_wms = []
    for i in range(5):
        layer_wms = LayerWMS(name=f"layer_wms_{i}")
        layer_wms.layer = f"wms_layer_{i}"
        layer_wms.ogc_server = ogc_server
        layers_wms.append(layer_wms)
        dbsession.add(layer_wms)
        layers_wms.append(layer_wms)

    roles = []
    for i in range(5):
        role = Role("secretary_" + str(i))
        role.functionalities = [
            functionalities["default_theme"][0],
        ]
        role.restrictionareas = [restrictionareas[0], restrictionareas[1]]
        dbsession.add(role)
        roles.append(role)

    dbsession.flush()

    group = LayerGroup(name="groups")
    dbsession.add(group)
    theme = Theme(name="theme")
    dbsession.add(theme)

    dbsession.flush()

    return {
        "ogc_server": ogc_server,
        "layers_wmts": layers_wmts,
        "layers_wms": layers_wms,
        "restrictionareas": restrictionareas,
        "interfaces": interfaces,
        "themes": [theme],
        "group": group,
        "roles": roles,
    }


@pytest.mark.usefixtures("edit_url_test_data", "test_app")
class TestUrlEdit(AbstractViewsTests):
    _prefix = "/admin/"

    def _get(self, test_app, tablename, pk):
        path = f"/{tablename}/{pk}"
        return test_app.get(path, status=200)

    def _check_link(self, test_app, resp, item, table, status):
        link = resp.html.select_one(f".form-group.item-{item} a")
        assert re.match(rf"http://localhost/admin/{table}/\d+", link["href"]) is not None
        test_app.get(link.get("href"), status=status)

    def test_layer_wms_edit(self, edit_url_test_data, test_app) -> None:
        resp = self._get(test_app, "admin/layers_wms", edit_url_test_data["layers_wms"][0].id)
        self._check_link(test_app, resp, "restrictionareas", "restriction_areas", 200)
        self._check_link(test_app, resp, "interfaces", "interfaces", 200)

    def test_layer_wmts_edit(self, edit_url_test_data, test_app) -> None:
        resp = self._get(test_app, "admin/layers_wmts", edit_url_test_data["layers_wmts"][0].id)
        self._check_link(test_app, resp, "restrictionareas", "restriction_areas", 200)
        self._check_link(test_app, resp, "interfaces", "interfaces", 200)

    def test_roles_edit(self, edit_url_test_data, test_app) -> None:
        resp = self._get(test_app, "admin/roles", edit_url_test_data["roles"][0].id)
        self._check_link(test_app, resp, "functionalities", "functionalities", 200)
        self._check_link(test_app, resp, "restrictionareas", "restriction_areas", 200)

    def test_themes_edit(self, edit_url_test_data, test_app) -> None:
        resp = self._get(test_app, "admin/themes", edit_url_test_data["themes"][0].id)
        self._check_link(test_app, resp, "functionalities", "functionalities", 200)
        self._check_link(test_app, resp, "interfaces", "interfaces", 200)
        self._check_link(test_app, resp, "restricted_roles", "roles", 200)
