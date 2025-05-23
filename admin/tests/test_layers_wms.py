# pylint: disable=no-self-use,unsubscriptable-object

import re

import pytest

from . import AbstractViewsTests, factory_build_layers, get_test_default_layers


@pytest.fixture
def layer_wms_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerWMS, OGCServer

    servers = [OGCServer(name=f"server_{i}") for i in range(4)]
    for i, server in enumerate(servers):
        server.url = f"https://wms.geo.admin.ch_{i}"
        server.image_type = "image/jpeg" if i % 2 == 0 else "image/png"

    def layer_builder(i):
        layer = LayerWMS(name=f"layer_wms_{i}")
        layer.layer = f"layer_{i}"
        layer.public = i % 2 == 1
        layer.geo_table = f"geotable_{i}"
        layer.ogc_server = servers[i % 4]
        layer.style = "décontrasté"
        return layer

    data = factory_build_layers(layer_builder, dbsession)
    data["servers"] = servers
    data["default"] = get_test_default_layers(dbsession, servers[1])

    dbsession.flush()

    return data


@pytest.mark.usefixtures("layer_wms_test_data", "test_app")
class TestLayerWMSViews(AbstractViewsTests):
    _prefix = "/admin/layers_wms"

    def test_index_rendering(self, test_app) -> None:
        resp = self.get(test_app)

        self.check_left_menu(resp, "WMS Layers")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name"),
            ("description", "Description"),
            ("public", "Public"),
            ("geo_table", "Geo table"),
            ("exclude_properties", "Exclude properties"),
            ("ogc_server", "OGC server"),
            ("layer", "WMS layer name"),
            ("style", "Style"),
            ("valid", "Valid"),
            ("invalid_reason", "Reason why I am not valid"),
            ("time_mode", "Time mode"),
            ("time_widget", "Time widget"),
            ("dimensions", "Dimensions", "false"),
            ("interfaces", "Interfaces"),
            ("restrictionareas", "Restriction areas", "false"),
            ("parents_relation", "Parents", "false"),
            ("metadatas", "Metadatas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_wms_test_data) -> None:
        json = self.check_search(test_app, sort="name", total=26)

        row = json["rows"][0]
        layer = layer_wms_test_data["layers"][0]

        assert layer.id == int(row["_id_"])
        assert layer.name == row["name"]
        assert row["restrictionareas"] == "restrictionarea_0, restrictionarea_2"
        assert row["ogc_server"] == "server_0"
        assert row["interfaces"] == "desktop, edit"
        assert row["dimensions"] == "Date: 2017, 1988; CLC: all"
        assert row["parents_relation"] == "layer_group_0, layer_group_3"
        assert row["metadatas"] == 'copyable: true, snappingConfig: {"tolerance": 50}'

    def test_grid_sort_on_ogc_server(self, test_app, layer_wms_test_data) -> None:
        json = self.check_search(test_app, sort="ogc_server")
        for i, layer in enumerate(
            sorted(layer_wms_test_data["layers"], key=lambda layer: (layer.ogc_server.name, layer.id)),
        ):
            if i == 10:
                break
            assert str(layer.id) == json["rows"][i]["_id_"]

    def test_grid_search(self, test_app) -> None:
        # check search on ogc_server.name
        self.check_search(test_app, "server_0", total=7)

        # check search on interfaces
        self.check_search(test_app, "mobile", total=9)

    def test_grid_empty_dimension(self, test_app, layer_wms_test_data) -> None:
        from c2cgeoportal_commons.models.main import Dimension

        layer = layer_wms_test_data["layers"][0]
        layer.dimensions.append(Dimension(name="Empty", value=None))
        json = self.check_search(test_app, layer.name, total=1)
        row = json["rows"][0]
        assert "Empty: NULL" in row["dimensions"]

    def test_new_no_default(self, test_app, layer_wms_test_data, dbsession) -> None:
        default_wms = layer_wms_test_data["default"]["wms"]
        default_wms.name = "so_can_I_not_be found"
        dbsession.flush()

        form = self.get_item(test_app, "new").form

        assert self.get_first_field_named(form, "id").value == ""
        assert self.get_first_field_named(form, "name").value == ""
        assert self.get_first_field_named(form, "layer").value == ""
        assert self.get_first_field_named(form, "ogc_server_id").value == ""
        assert self.get_first_field_named(form, "time_mode").value == "disabled"
        assert self.get_first_field_named(form, "time_widget").value == "slider"

    def test_new_default(self, test_app, layer_wms_test_data) -> None:
        default_wms = layer_wms_test_data["default"]["wms"]

        form = self.get_item(test_app, "new").form

        assert self.get_first_field_named(form, "id").value == ""
        assert self.get_first_field_named(form, "name").value == ""
        assert self.get_first_field_named(form, "layer").value == ""
        assert str(default_wms.ogc_server.id) == self.get_first_field_named(form, "ogc_server_id").value
        assert default_wms.time_mode == self.get_first_field_named(form, "time_mode").value
        assert default_wms.time_widget == self.get_first_field_named(form, "time_widget").value

    def test_base_edit(self, test_app, layer_wms_test_data) -> None:
        layer = layer_wms_test_data["layers"][10]

        form = self.get_item(test_app, layer.id).form

        assert self.get_first_field_named(form, "name").value == "layer_wms_10"
        assert self.get_first_field_named(form, "description").value == ""

    def test_public_checkbox_edit(self, test_app, layer_wms_test_data) -> None:
        layer = layer_wms_test_data["layers"][10]
        form = self.get_item(test_app, layer.id).form
        assert not form["public"].checked

        layer = layer_wms_test_data["layers"][11]
        form = self.get_item(test_app, layer.id).form
        assert form["public"].checked

    def test_edit(self, test_app, layer_wms_test_data, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Log, LogAction

        layer = layer_wms_test_data["layers"][0]

        form = self.get_item(test_app, layer.id).form

        assert str(layer.id) == self.get_first_field_named(form, "id").value
        assert self.get_first_field_named(form, "id").attrs["type"] == "hidden"
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is False
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.ogc_server_id) == form["ogc_server_id"].value
        assert str(layer.layer or "") == form["layer"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer.time_mode) == form["time_mode"].value
        assert str(layer.time_widget) == form["time_widget"].value

        interfaces = layer_wms_test_data["interfaces"]
        assert {interfaces[0].id, interfaces[2].id} == {i.id for i in layer.interfaces}
        self._check_interfaces(form, interfaces, layer)

        ras = layer_wms_test_data["restrictionareas"]
        assert {ras[0].id, ras[2].id} == {i.id for i in layer.restrictionareas}
        self._check_restrictionsareas(form, ras, layer)

        new_values = {
            "name": "new_name",
            "description": "new description",
            "public": True,
            "geo_table": "new_geo_table",
            "exclude_properties": "property1,property2",
            "ogc_server_id": str(layer_wms_test_data["servers"][1].id),
            "layer": "new_wmslayername",
            "style": "new_style",
            "time_mode": "range",
            "time_widget": "datepicker",
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
        assert log.element_type == "layer_wms"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_submit_new(self, dbsession, test_app, layer_wms_test_data) -> None:
        from c2cgeoportal_commons.models.main import LayerWMS, Log, LogAction

        resp = test_app.post(
            "/admin/layers_wms/new",
            {
                "name": "new_name",
                "description": "new description",
                "public": True,
                "geo_table": "new_geo_table",
                "exclude_properties": "property1,property2",
                "ogc_server_id": str(layer_wms_test_data["servers"][1].id),
                "layer": "new_wmslayername",
                "style": "new_style",
                "time_mode": "range",
                "time_widget": "datepicker",
            },
            status=302,
        )

        layer = dbsession.query(LayerWMS).filter(LayerWMS.name == "new_name").one()
        assert str(layer.id) == re.match(
            r"http://localhost/admin/layers_wms/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.INSERT
        assert log.element_type == "layer_wms"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_duplicate(self, layer_wms_test_data, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import LayerWMS

        layer = layer_wms_test_data["layers"][3]

        resp = test_app.get(f"/admin/layers_wms/{layer.id}/duplicate", status=200)
        form = resp.form

        assert self.get_first_field_named(form, "id").value == ""
        assert layer.name == self.get_first_field_named(form, "name").value
        assert str(layer.description or "") == self.get_first_field_named(form, "description").value
        assert layer.public is True
        assert layer.public == form["public"].checked
        assert str(layer.geo_table or "") == form["geo_table"].value
        assert str(layer.exclude_properties or "") == form["exclude_properties"].value
        assert str(layer.ogc_server_id) == form["ogc_server_id"].value
        assert str(layer.layer or "") == form["layer"].value
        assert str(layer.style or "") == form["style"].value
        assert str(layer.time_mode) == form["time_mode"].value
        assert str(layer.time_widget) == form["time_widget"].value
        interfaces = layer_wms_test_data["interfaces"]
        assert {interfaces[3].id, interfaces[1].id} == {i.id for i in layer.interfaces}
        self._check_interfaces(form, interfaces, layer)

        ras = layer_wms_test_data["restrictionareas"]
        assert {ras[3].id, ras[0].id} == {i.id for i in layer.restrictionareas}
        self._check_restrictionsareas(form, ras, layer)

        self._check_dimensions(resp.html, layer.dimensions, duplicated=True)

        self.set_first_field_named(form, "name", "clone")
        resp = form.submit("submit")

        layer = dbsession.query(LayerWMS).filter(LayerWMS.name == "clone").one()
        assert str(layer.id) == re.match(
            r"http://localhost/admin/layers_wms/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)
        assert layer.id == layer.dimensions[0].layer_id
        assert layer.id == layer.metadatas[0].item_id
        assert layer_wms_test_data["layers"][3].metadatas[0].name == layer.metadatas[0].name
        assert layer_wms_test_data["layers"][3].metadatas[1].name == layer.metadatas[1].name

    def test_convert_common_fields_copied(self, layer_wms_test_data, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import LayerWMS, LayerWMTS

        layer = layer_wms_test_data["layers"][3]

        assert dbsession.query(LayerWMTS).filter(LayerWMTS.name == layer.name).count() == 0
        assert dbsession.query(LayerWMS).filter(LayerWMS.name == layer.name).count() == 1

        resp = test_app.post(f"/admin/layers_wms/{layer.id}/convert_to_wmts", status=200)
        assert resp.json["success"]
        assert f"http://localhost/admin/layers_wmts/{layer.id}?msg_col=submit_ok" == resp.json["redirect"]

        assert dbsession.query(LayerWMTS).filter(LayerWMTS.name == layer.name).count() == 1
        assert dbsession.query(LayerWMS).filter(LayerWMS.name == layer.name).count() == 0

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
        assert layer_wms_test_data["default"]["wmts"].url == self.get_first_field_named(form, "url").value
        assert layer_wms_test_data["default"]["wmts"].matrix_set == form["matrix_set"].value

        interfaces = layer_wms_test_data["interfaces"]
        self._check_interfaces(form, interfaces, layer)
        ras = layer_wms_test_data["restrictionareas"]
        self._check_restrictionsareas(form, ras, layer)
        self._check_dimensions(resp.html, layer.dimensions)

        assert (
            resp.html.find("div", {"class": "msg-lbl"}).getText()
            == "Your submission has been taken into account."
        )

    def test_convert_image_type_from_ogcserver(self, layer_wms_test_data, test_app) -> None:
        layer = layer_wms_test_data["layers"][3]

        resp = test_app.post(f"/admin/layers_wms/{layer.id}/convert_to_wmts", status=200)
        assert resp.json["success"]
        assert f"http://localhost/admin/layers_wmts/{layer.id}?msg_col=submit_ok" == resp.json["redirect"]

        resp = test_app.get(resp.json["redirect"], status=200)
        assert resp.form["image_type"].value == "image/png"

        layer = layer_wms_test_data["layers"][2]
        resp = test_app.post(f"/admin/layers_wms/{layer.id}/convert_to_wmts", status=200)
        assert resp.json["success"]
        assert f"http://localhost/admin/layers_wmts/{layer.id}?msg_col=submit_ok" == resp.json["redirect"]

        resp = test_app.get(resp.json["redirect"], status=200)
        assert resp.form["image_type"].value == "image/jpeg"

    def test_convert_without_wmts_defaults(self, test_app, layer_wms_test_data, dbsession) -> None:
        from c2cgeoportal_commons.models.main import LayerWMTS, Log, LogAction

        dbsession.delete(LayerWMTS.get_default(dbsession))
        layer = layer_wms_test_data["layers"][3]
        test_app.post(f"/admin/layers_wms/{layer.id}/convert_to_wmts", status=200)

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.CONVERT_TO_WMTS
        assert log.element_type == "layer_wms"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_unicity_validator(self, layer_wms_test_data, test_app) -> None:
        layer = layer_wms_test_data["layers"][2]
        resp = test_app.get(f"/admin/layers_wms/{layer.id}/duplicate", status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{layer.name} is already used.")

    def test_unicity_validator_does_not_matter_amongst_cousin(
        self,
        layer_wms_test_data,
        test_app,
        dbsession,
    ) -> None:
        from c2cgeoportal_commons.models.main import LayerGroup, LayerWMS

        assert dbsession.query(LayerGroup).filter(LayerGroup.name == "layer_group_0").count() == 1

        assert dbsession.query(LayerWMS).filter(LayerWMS.name == "layer_group_0").one_or_none() is None

        layer = layer_wms_test_data["layers"][2]
        resp = test_app.get(f"/admin/layers_wms/{layer.id}/duplicate", status=200)
        self.set_first_field_named(resp.form, "name", "layer_group_0")
        resp = resp.form.submit("submit")

        # layer = dbsession.query(LayerWMS). \
        #     filter(LayerWMS.name == 'layer_group_0'). \
        #     one()
        # assert str(layer.id) == re.match('http://localhost/admin/layers_wms/(.*)', resp.location).group(1)

    def test_delete(self, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import (
            Layer,
            LayerWMS,
            Log,
            LogAction,
            TreeItem,
        )

        layer = dbsession.query(LayerWMS).first()

        test_app.delete(f"/admin/layers_wms/{layer.id}", status=200)

        assert dbsession.query(LayerWMS).get(layer.id) is None
        assert dbsession.query(Layer).get(layer.id) is None
        assert dbsession.query(TreeItem).get(layer.id) is None

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.DELETE
        assert log.element_type == "layer_wms"
        assert log.element_id == layer.id
        assert log.element_name == layer.name
        assert log.username == "test_user"

    def test_submit_new_no_layer_name(self, test_app, layer_wms_test_data, dbsession) -> None:
        resp = test_app.post(
            "/admin/layers_wms/new",
            {
                "name": "new_name",
                "description": "new description",
                "public": True,
                "geo_table": "new_geo_table",
                "exclude_properties": "property1,property2",
                "ogc_server_id": str(layer_wms_test_data["servers"][1].id),
                "style": "new_style",
                "time_mode": "range",
                "time_widget": "datepicker",
            },
            status=200,
        )

        assert (
            resp.html.select_one('div[class="error-msg-lbl"]').text
            == "There was a problem with your submission"
        )
        assert (
            resp.html.select_one('div[class="error-msg-detail"]').text == "Errors have been highlighted below"
        )
        assert sorted(
            (x.select_one("label").text.strip()) for x in resp.html.select("[class~='has-error']")
        ) == ["WMS layer name"]
