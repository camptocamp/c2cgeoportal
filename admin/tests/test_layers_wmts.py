# pylint: disable=no-self-use

import re

import pytest

from . import AbstractViewsTests, factory_build_layers, get_test_default_layers


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def layer_wmts_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerWMTS, OGCServer

    server = OGCServer(name="server_1")
    server.url = "http://wms.geo.admin.ch_1"
    server.image_type = "image/png"

    def layer_builder(i):
        name = "layer_wmts_{}".format(i)
        layer = LayerWMTS(name=name)
        layer.layer = name
        layer.url = "https:///wms.geo.admin.ch_{}.org?service=wms&request=GetCapabilities".format(i)
        layer.public = 1 == i % 2
        layer.geo_table = "geotable_{}".format(i)
        layer.image_type = "image/jpeg"
        layer.style = "décontrasté"
        return layer

    datas = factory_build_layers(layer_builder, dbsession)
    datas["default"] = get_test_default_layers(dbsession, server)

    dbsession.flush()

    yield datas


@pytest.mark.usefixtures("layer_wmts_test_data", "test_app")
class TestLayerWMTS(AbstractViewsTests):

    _prefix = "/admin/layers_wmts"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "WMTS Layers")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name", "true"),
            ("description", "Description", "true"),
            ("public", "Public", "true"),
            ("geo_table", "Geo table", "true"),
            ("exclude_properties", "Exclude properties", "true"),
            ("url", "GetCapabilities URL", "true"),
            ("layer", "WMTS layer name", "true"),
            ("style", "Style", "true"),
            ("matrix_set", "Matrix set", "true"),
            ("image_type", "Image type", "true"),
            ("dimensions", "Dimensions", "false"),
            ("interfaces", "Interfaces", "true"),
            ("restrictionareas", "Restriction areas", "false"),
            ("parents_relation", "Parents", "false"),
            ("metadatas", "Metadatas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_wmts_test_data):
        json = self.check_search(test_app, sort="name")

        row = json["rows"][0]
        layer = layer_wmts_test_data["layers"][0]

        assert layer.id == int(row["_id_"])
        assert layer.name == row["name"]

    def test_new_no_default(self, test_app, layer_wmts_test_data, dbsession):
        default_wmts = layer_wmts_test_data["default"]["wmts"]
        default_wmts.name = "so_can_I_not_be found"
        dbsession.flush()

        form = self.get_item(test_app, "new").form

        assert "" == self.get_first_field_named(form, "id").value
        assert "" == self.get_first_field_named(form, "name").value
        assert "" == self.get_first_field_named(form, "layer").value
        assert "" == self.get_first_field_named(form, "url").value
        assert "" == self.get_first_field_named(form, "matrix_set").value

    def test_new_default(self, test_app, layer_wmts_test_data):
        default_wmts = layer_wmts_test_data["default"]["wmts"]

        form = self.get_item(test_app, "new").form

        assert "" == self.get_first_field_named(form, "id").value
        assert "" == self.get_first_field_named(form, "name").value
        assert "" == self.get_first_field_named(form, "layer").value
        assert default_wmts.url == self.get_first_field_named(form, "url").value
        assert default_wmts.matrix_set == self.get_first_field_named(form, "matrix_set").value

    def test_edit(self, test_app, layer_wmts_test_data, dbsession):
        layer = layer_wmts_test_data["layers"][0]

        form = self.get_item(test_app, layer.id).form

        assert str(layer.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is False
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.url or "") == self.get_first_field_named(form, "url").value
        assert str(layer.layer or "") == form["layer"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer.matrix_set or "") == form["matrix_set"].value
        assert str(layer.image_type or "") == form["image_type"].value

        interfaces = layer_wmts_test_data["interfaces"]
        assert set((interfaces[0].id, interfaces[2].id)) == set(i.id for i in layer.interfaces)
        self._check_interfaces(form, interfaces, layer)

        ras = layer_wmts_test_data["restrictionareas"]
        assert set((ras[0].id, ras[2].id)) == set(i.id for i in layer.restrictionareas)
        self._check_restrictionsareas(form, ras, layer)

        new_values = {
            "name": "new_name",
            "description": "new description",
            "public": True,
            "geo_table": "new_geo_table",
            "exclude_properties": "property1,property2",
            "url": "new_url",
            "layer": "new_wmslayername",
            "style": "new_style",
            "matrix_set": "new_matrix_set",
            "image_type": "image/png",
        }

        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)
        form["interfaces"] = [interfaces[1].id, interfaces[3].id]
        form["restrictionareas"] = [ras[1].id, ras[3].id]

        resp = form.submit("submit")
        assert str(layer.id) == re.match(
            r"http://localhost{}/(.*)\?msg_col=submit_ok".format(self._prefix), resp.location
        ).group(1)

        dbsession.expire(layer)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(layer, key)
            else:
                assert str(value or "") == str(getattr(layer, key) or "")
        assert set([interfaces[1].id, interfaces[3].id]) == set(
            [interface.id for interface in layer.interfaces]
        )
        assert set([ras[1].id, ras[3].id]) == set([ra.id for ra in layer.restrictionareas])

    def test_duplicate(self, layer_wmts_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMTS

        layer = layer_wmts_test_data["layers"][3]

        resp = test_app.get("/admin/layers_wmts/{}/duplicate".format(layer.id), status=200)
        form = resp.form

        assert "" == self.get_first_field_named(form, "id").value
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is True
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.layer or "") == form["layer"].value
        assert str(layer.style or "") == form["style"].value

        ras = layer_wmts_test_data["restrictionareas"]
        self._check_restrictionsareas(form, ras, layer)

        self.set_first_field_named(form, "name", "clone")
        resp = form.submit("submit")

        layer = dbsession.query(LayerWMTS).filter(LayerWMTS.name == "clone").one()
        assert str(layer.id) == re.match(
            r"http://localhost/admin/layers_wmts/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMTS, Layer, TreeItem

        layer_id = dbsession.query(LayerWMTS.id).first().id

        test_app.delete("/admin/layers_wmts/{}".format(layer_id), status=200)

        assert dbsession.query(LayerWMTS).get(layer_id) is None
        assert dbsession.query(Layer).get(layer_id) is None
        assert dbsession.query(TreeItem).get(layer_id) is None

    def test_unicity_validator(self, layer_wmts_test_data, test_app):
        layer = layer_wmts_test_data["layers"][2]
        resp = test_app.get("/admin/layers_wmts/{}/duplicate".format(layer.id), status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, "{} is already used.".format(layer.name))

    def test_convert_common_fields_copied(self, layer_wmts_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMTS, LayerWMS

        layer = layer_wmts_test_data["layers"][3]

        assert 0 == dbsession.query(LayerWMS).filter(LayerWMS.name == layer.name).count()
        assert 1 == dbsession.query(LayerWMTS).filter(LayerWMTS.name == layer.name).count()

        resp = test_app.post("/admin/layers_wmts/{}/convert_to_wms".format(layer.id), status=200)
        assert (
            "http://localhost/admin/layers_wms/{}?msg_col=submit_ok".format(layer.id) == resp.json["redirect"]
        )

        assert 1 == dbsession.query(LayerWMS).filter(LayerWMS.name == layer.name).count()
        assert 0 == dbsession.query(LayerWMTS).filter(LayerWMTS.name == layer.name).count()

        resp = test_app.get(resp.json["redirect"], status=200)
        form = resp.form

        assert str(layer.id) == self.get_first_field_named(form, "id").value
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is True
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.layer or "") == form["layer"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer_wmts_test_data["default"]["wms"].ogc_server_id) == form["ogc_server_id"].value
        assert str(layer_wmts_test_data["default"]["wms"].time_mode) == form["time_mode"].value
        assert str(layer_wmts_test_data["default"]["wms"].time_widget) == form["time_widget"].value
        interfaces = layer_wmts_test_data["interfaces"]
        self._check_interfaces(form, interfaces, layer)
        ras = layer_wmts_test_data["restrictionareas"]
        self._check_restrictionsareas(form, ras, layer)
        self._check_dimensions(resp.html, layer.dimensions)
        assert (
            "Your submission has been taken into account."
            == resp.html.find("div", {"class": "msg-lbl"}).getText()
        )

    def test_convert_without_wms_defaults(self, test_app, layer_wmts_test_data, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS

        dbsession.delete(LayerWMS.get_default(dbsession))
        layer = layer_wmts_test_data["layers"][3]
        test_app.post("/admin/layers_wmts/{}/convert_to_wms".format(layer.id), status=200)
