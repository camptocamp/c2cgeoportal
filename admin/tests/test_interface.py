# pylint: disable=no-self-use

import re

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def interface_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Interface, Theme, OGCServer, LayerWMS

    themes = []
    for i in range(0, 5):
        theme = Theme(name="theme_{}".format(i), ordering=1)
        themes.append(theme)

    servers = [OGCServer(name="server_{}".format(i)) for i in range(0, 4)]

    layers = []
    for i in range(0, 15):
        layer = LayerWMS(name="layer_wms_{}".format(i))
        layer.public = 1 == i % 2
        layer.ogc_server = servers[i % 4]
        dbsession.add(layer)
        layers.append(layer)

    interfaces = []
    for i in range(0, 5):
        interface = Interface(name="interface_{}".format(i), description="description_{}".format(i))
        interface.themes = [themes[i % 2], themes[(i + 5) % 5]]
        interface.layers = [layers[i % 2], layers[(i + 4) % 5]]

        dbsession.add(interface)
        interfaces.append(interface)

    dbsession.flush()

    yield {"interfaces": interfaces}


@pytest.mark.usefixtures("interface_test_data", "test_app")
class TestInterface(AbstractViewsTests):

    _prefix = "/admin/interfaces"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Interfaces")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name", "true"),
            ("description", "Description", "true"),
            ("layers", "Layers", "false"),
            ("theme", "Themes", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, interface_test_data):
        json = self.check_search(test_app)

        first_row = json["rows"][0]
        first_interface = interface_test_data["interfaces"][0]

        assert first_interface.id == int(first_row["_id_"])
        assert first_interface.name == first_row["name"]
        assert first_interface.description == first_row["description"]
        assert len(first_interface.layers) == 2
        assert first_interface.layers[1].name == "layer_wms_4"
        assert len(first_interface.themes) == 2
        assert first_interface.themes[1].name == "theme_0"

    def test_grid_search(self, test_app):
        # search on interface name
        self.check_search(test_app, "interface_0", total=1)

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import Interface

        resp = test_app.post(
            "/admin/interfaces/new", {"name": "new_name", "description": "new description"}, status=302
        )

        interface = dbsession.query(Interface).filter(Interface.name == "new_name").one()
        assert str(interface.id) == re.match(
            r"http://localhost/admin/interfaces/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert interface.name == "new_name"

    def test_edit(self, test_app, interface_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Interface

        interface = interface_test_data["interfaces"][0]
        descriptions = "{}, {}".format(
            interface_test_data["interfaces"][0].description, interface_test_data["interfaces"][1].description
        )
        resp = test_app.get("/admin/interfaces/{}".format(interface.id), status=200)
        form = resp.form
        form["description"] = descriptions
        assert str(interface.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert interface.name == self.get_first_field_named(form, "name").value
        assert form.submit().status_int == 302
        assert len(dbsession.query(Interface).filter(Interface.description == descriptions).all()) == 1

    def test_delete(self, test_app, interface_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Interface

        interface = interface_test_data["interfaces"][0]
        test_app.delete("/admin/interfaces/{}".format(interface.id), status=200)
        assert len(dbsession.query(Interface).filter(Interface.id == interface.id).all()) == 0

    def test_duplicate(self, interface_test_data, test_app):
        interface = interface_test_data["interfaces"][3]
        resp = test_app.get("/admin/interfaces/{}/duplicate".format(interface.id), status=200)
        form = resp.form
        assert "" == self.get_first_field_named(form, "id").value
        assert str(interface.description or "") == "description_3"
        assert form.submit().status_int == 302
