# pylint: disable=no-self-use

import re

import pytest

from . import AbstractViewsTests, factory_build_layers, get_test_default_layers


@pytest.fixture
def layer_vectortiles_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerVectorTiles

    def layer_builder(i):
        name = f"layer_vectortiles_{i}"
        layer = LayerVectorTiles(name=name)
        layer.layer = name
        layer.public = i % 2 == 1
        layer.style = "https://vectortiles-staging.geoportail.lu/styles/roadmap/style.json"
        layer.xyz = "https://vectortiles-staging.geoportail.lu/styles/roadmap/{z}/{x}/{y}.png"
        return layer

    data = factory_build_layers(layer_builder, dbsession)
    data["default"] = get_test_default_layers(dbsession, None)

    dbsession.flush()

    return data


@pytest.mark.usefixtures("layer_vectortiles_test_data", "test_app")
class TestLayerVectortiles(AbstractViewsTests):
    _prefix = "/admin/layers_vectortiles"

    def test_index_rendering(self, test_app) -> None:
        resp = self.get(test_app)

        self.check_left_menu(resp, "Vector Tiles Layers")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name"),
            ("description", "Description"),
            ("public", "Public"),
            ("geo_table", "Geo table"),
            ("exclude_properties", "Exclude properties"),
            ("style", "Style"),
            ("xyz", "Raster URL"),
            ("dimensions", "Dimensions", "false"),
            ("interfaces", "Interfaces"),
            ("restrictionareas", "Restriction areas", "false"),
            ("parents_relation", "Parents", "false"),
            ("metadatas", "Metadatas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_vectortiles_test_data) -> None:
        json = self.check_search(test_app, sort="name")

        row = json["rows"][0]
        layer = layer_vectortiles_test_data["layers"][0]

        assert layer.id == int(row["_id_"])
        assert layer.name == row["name"]

    def test_new(self, test_app, layer_vectortiles_test_data, dbsession) -> None:
        default_vectortiles = layer_vectortiles_test_data["default"]["vectortiles"]
        default_vectortiles.name = "so can I not be found"
        dbsession.flush()

        form = self.get_item(test_app, "new").form

        assert self.get_first_field_named(form, "id").value == ""
        assert self.get_first_field_named(form, "name").value == ""
        assert self.get_first_field_named(form, "style").value == ""
        assert self.get_first_field_named(form, "xyz").value == ""

    def test_grid_search(self, test_app) -> None:
        self.check_search(test_app, "layer_vectortiles_10", total=1)

    def test_base_edit(self, test_app, layer_vectortiles_test_data) -> None:
        layer = layer_vectortiles_test_data["layers"][10]

        form = self.get_item(test_app, layer.id).form

        assert self.get_first_field_named(form, "name").value == "layer_vectortiles_10"
        assert self.get_first_field_named(form, "description").value == ""

    def test_public_checkbox_edit(self, test_app, layer_vectortiles_test_data) -> None:
        layer = layer_vectortiles_test_data["layers"][10]
        form = self.get_item(test_app, layer.id).form
        assert not form["public"].checked

        layer = layer_vectortiles_test_data["layers"][11]
        form = self.get_item(test_app, layer.id).form
        assert form["public"].checked

    def test_edit(self, test_app, layer_vectortiles_test_data, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Log, LogAction

        layer = layer_vectortiles_test_data["layers"][0]

        form = self.get_item(test_app, layer.id).form

        assert str(layer.id) == self.get_first_field_named(form, "id").value
        assert self.get_first_field_named(form, "id").attrs["type"] == "hidden"
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is False
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer.xyz or "") == form["xyz"].value

        interfaces = layer_vectortiles_test_data["interfaces"]
        assert {interfaces[0].id, interfaces[2].id} == {i.id for i in layer.interfaces}
        self._check_interfaces(form, interfaces, layer)

        ras = layer_vectortiles_test_data["restrictionareas"]
        assert {ras[0].id, ras[2].id} == {i.id for i in layer.restrictionareas}
        self._check_restrictionsareas(form, ras, layer)

        new_values = {
            "name": "new_name",
            "description": "new description",
            "public": True,
            "geo_table": "new_geo_table",
            "exclude_properties": "property1,property2",
            "style": "https://new_style.json",
            "xyz": "https://new_style/{x}/{y}/{z}.png",
        }

        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)
        form["interfaces"] = [interfaces[1].id, interfaces[3].id]
        form["restrictionareas"] = [ras[1].id, ras[3].id]

        resp = form.submit("submit")
        assert str(layer.id) == re.match(
            rf"http://localhost{self._prefix}/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        dbsession.expire(layer)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(layer, key)
            else:
                assert str(value or "") == str(getattr(layer, key) or "")
        assert {interfaces[1].id, interfaces[3].id} == {interface.id for interface in layer.interfaces}
        assert {ras[1].id, ras[3].id} == {ra.id for ra in layer.restrictionareas}

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "layer_vectortiles"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_submit_new(self, dbsession, test_app, layer_vectortiles_test_data) -> None:
        from c2cgeoportal_commons.models.main import LayerVectorTiles, Log, LogAction

        resp = test_app.post(
            "/admin/layers_vectortiles/new",
            {
                "name": "new_name",
                "description": "new description",
                "public": True,
                "style": "https://new_style/styles/layer/style.json",
                "xyz": "https://new_style/styles/layer/{z}/{x}/{y}.png",
            },
            status=302,
        )

        layer = dbsession.query(LayerVectorTiles).filter(LayerVectorTiles.name == "new_name").one()
        assert str(layer.id) == re.match(
            r"http://localhost/admin/layers_vectortiles/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.INSERT
        assert log.element_type == "layer_vectortiles"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_duplicate(self, layer_vectortiles_test_data, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import LayerVectorTiles

        layer = layer_vectortiles_test_data["layers"][3]

        resp = test_app.get(f"/admin/layers_vectortiles/{layer.id}/duplicate", status=200)
        form = resp.form

        assert self.get_first_field_named(form, "id").value == ""
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is True
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer.xyz or "") == form["xyz"].value
        interfaces = layer_vectortiles_test_data["interfaces"]
        assert {interfaces[3].id, interfaces[1].id} == {i.id for i in layer.interfaces}
        self._check_interfaces(form, interfaces, layer)

        self.set_first_field_named(form, "name", "clone")
        resp = form.submit("submit")

        layer = dbsession.query(LayerVectorTiles).filter(LayerVectorTiles.name == "clone").one()
        assert str(layer.id) == re.match(
            r"http://localhost/admin/layers_vectortiles/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        assert layer.id == layer.metadatas[0].item_id
        assert layer_vectortiles_test_data["layers"][3].metadatas[0].name == layer.metadatas[0].name
        assert layer_vectortiles_test_data["layers"][3].metadatas[1].name == layer.metadatas[1].name

    def test_delete(self, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import (
            Layer,
            LayerVectorTiles,
            Log,
            LogAction,
            TreeItem,
        )

        layer = dbsession.query(LayerVectorTiles).first()

        test_app.delete(f"/admin/layers_vectortiles/{layer.id}", status=200)

        assert dbsession.query(LayerVectorTiles).get(layer.id) is None
        assert dbsession.query(Layer).get(layer.id) is None
        assert dbsession.query(TreeItem).get(layer.id) is None

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.DELETE
        assert log.element_type == "layer_vectortiles"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"
