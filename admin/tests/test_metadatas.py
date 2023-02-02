# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def metadatas_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerGroup, LayerWMS, LayerWMTS, Metadata, OGCServer, Theme

    ogc_server = OGCServer(name="ogc_server")

    layer_wms = LayerWMS(name="layer_wms")
    layer_wms.layer = "wms_layer"
    layer_wms.ogc_server = ogc_server
    layer_wms.metadatas = [
        Metadata(name, value)
        for name, value in [
            ("_string", "ceci est un test"),
            ("_liste", "valeur1,valeur2"),
            ("_boolean", "true"),
            ("_int", "1"),
            ("_float", "2.5"),
            ("_url", "https://localhost/test.html"),
            ("_json", '{"key":"value"}'),
            ("_color", "#FFFFFF"),
            ("_unknown", "This is an unknown format"),
        ]
    ]
    for metadata in layer_wms.metadatas:
        metadata.item = layer_wms
    dbsession.add(layer_wms)

    layer_wmts = LayerWMTS(name="layer_wmts")
    layer_wmts.url = "https://localhost"
    layer_wmts.layer = "wmts_layer"
    dbsession.add(layer_wmts)

    theme = Theme(name="theme")
    dbsession.add(theme)

    group = LayerGroup(name="groups")
    dbsession.add(group)

    dbsession.flush()

    yield {
        "ogc_server": ogc_server,
        "layer_wms": layer_wms,
        "layer_wmts": layer_wmts,
        "theme": theme,
        "group": group,
    }


@pytest.mark.usefixtures("metadatas_test_data", "test_app")
class TestMetadatasView(AbstractViewsTests):
    _prefix = "/admin/"

    def __metadata_ui_types(self):
        return ("string", "liste", "boolean", "int", "float", "url", "json")

    def __metadata_ui_type(self, test_app, name):
        settings = test_app.app.registry.settings
        return next(
            (
                m.get("type", "string")
                for m in settings["admin_interface"]["available_metadata"]
                if m["name"] == name and m["type"] in self.__metadata_ui_types()
            ),
            "string",
        )

    def expected_value(self, test_app, metadata):
        if self.__metadata_ui_type(test_app, metadata.name) == "boolean":
            if metadata.value == "true":
                return True
            if metadata.value == "false":
                return False
            return None
        return metadata.value

    def _check_metadatas(self, test_app, item, metadatas, model):
        from c2cgeoportal_admin.schemas.metadata import metadata_definitions

        settings = test_app.app.registry.settings
        self._check_sequence(
            item,
            [
                [
                    {"name": "id", "value": str(m.id), "hidden": True},
                    {
                        "name": "name",
                        "value": [
                            {"text": s_m["name"], "value": s_m["name"], "selected": s_m["name"] == m.name}
                            for s_m in sorted(metadata_definitions(settings, model), key=lambda m: m["name"])
                        ],
                        "label": "Name",
                    },
                    {
                        "name": self.__metadata_ui_type(test_app, m.name),
                        "value": self.expected_value(test_app, m),
                    },
                    {"name": "description", "value": m.description, "label": "Description"},
                ]
                for m in metadatas
            ],
        )

    def _post_metadata(self, test_app, url, base_mapping, name, value, status):
        return test_app.post(
            url,
            base_mapping
            + (
                ("__start__", "metadatas:sequence"),
                ("__start__", "metadata:mapping"),
                ("name", name),
                (self.__metadata_ui_type(test_app, name), value),
                ("__end__", "metadata:mapping"),
                ("__end__", "metadatas:sequence"),
            ),
            status=status,
        )

    def _post_invalid_metadata(self, test_app, url, base_mapping, name, value, error_msg):
        resp = self._post_metadata(test_app, url, base_mapping, name, value, 200)
        assert (
            error_msg
            == resp.html.select_one(f".item-{self.__metadata_ui_type(test_app, name)} .help-block")
            .getText()
            .strip()
        )
        return resp

    @staticmethod
    def _base_metadata_params(metadatas_test_data):
        return (
            ("name", "new_name"),
            ("ogc_server_id", metadatas_test_data["ogc_server"].id),
            ("layer", "new_wmslayername"),
        )

    def test_invalid_float_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_float",
            "number",
            '"number" is not a number',
        )

    def test_get_true_boolean_metadata(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import LayerWMS

        metadatas_test_data["layer_wms"].get_metadata("_boolean")[0].value = "true"
        self._test_edit_treeitem("layers_wms", metadatas_test_data["layer_wms"], test_app, LayerWMS)

    def test_get_false_boolean_metadata(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import LayerWMS

        metadatas_test_data["layer_wms"].get_metadata("_boolean")[0].value = "false"
        self._test_edit_treeitem("layers_wms", metadatas_test_data["layer_wms"], test_app, LayerWMS)

    def test_post_true_boolean_metadata(self, test_app, metadatas_test_data, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS

        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_boolean",
            "true",
            302,
        )
        layer = dbsession.query(LayerWMS).filter(LayerWMS.name == "new_name").one()
        assert layer.get_metadata("_boolean")[0].value == "true"

    def test_post_false_boolean_metadata(self, test_app, metadatas_test_data, dbsession):
        from c2cgeoportal_commons.models.main import LayerWMS

        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_boolean",
            "false",
            302,
        )
        layer = dbsession.query(LayerWMS).filter(LayerWMS.name == "new_name").one()
        assert layer.get_metadata("_boolean")[0].value == "false"

    def test_valid_float_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_float",
            "2.5",
            302,
        )

    def test_invalid_int_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_int",
            "number",
            '"number" is not a number',
        )

    def test_valid_int_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_int",
            "2",
            302,
        )

    def test_invalid_url_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_url",
            "gnagnagna",
            "Must be a URL",
        )

    @pytest.mark.parametrize(
        "url",
        [
            "www.111111111111111111111111111111111111111111111111111111111111.com",
            "static://static/img/cadastre.jpeg",
        ],
    )
    def test_valid_url_metadata(self, test_app, metadatas_test_data, url):
        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_url",
            url,
            302,
        )

    def test_invalid_json_metadata(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_json",
            """{"colors": [{
                "color": "black",
                "category": "hue",
                "type": "primary",
                "code": {
                    "rgba": [255,255,255,1,
                    "hex": "#000"
                }
            }]}""",
            "Parser report: \"Expecting ',' delimiter: line 7 column 26 (char 213)\"",
        )

    def test_valid_json_metadata(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_json",
            """{"colors": [{
                "color": "black",
                "category": "hue",
                "type": "primary",
                "code": {
                    "rgba": [255,255,255,1],
                    "hex": "#000"
                }
            }]}""",
            302,
        )

    def test_invalid_color(self, test_app, metadatas_test_data):
        self._post_invalid_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_color",
            "#W007DCD",
            "Expecting hex format for color, e.g. #007DCD",
        )

    def test_valid_color(self, test_app, metadatas_test_data):
        self._post_metadata(
            test_app,
            "/admin/layers_wms/new",
            self._base_metadata_params(metadatas_test_data),
            "_color",
            "#007DCD",
            302,
        )

    def _test_edit_treeitem(self, prefix, item, test_app, model):
        resp = self.get(test_app, f"{prefix}/{item.id}")
        self._check_metadatas(test_app, resp.html.select_one(".item-metadatas"), item.metadatas, model)
        resp.form.submit("submit", status=302)

    def test_layer_wms_metadatas(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import LayerWMS

        self._test_edit_treeitem("layers_wms", metadatas_test_data["layer_wms"], test_app, LayerWMS)

    def test_layer_wmts_metadatas(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import LayerWMTS

        self._test_edit_treeitem("layers_wmts", metadatas_test_data["layer_wmts"], test_app, LayerWMTS)

    def test_theme_metadatas(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import Theme

        self._test_edit_treeitem("themes", metadatas_test_data["theme"], test_app, Theme)

    def test_group_metadatas(self, metadatas_test_data, test_app):
        from c2cgeoportal_commons.models.main import LayerGroup

        self._test_edit_treeitem("layer_groups", metadatas_test_data["group"], test_app, LayerGroup)

    def test_undefined_metadata(self, metadatas_test_data, test_app):
        """
        Undefined metadata must be kept intact across submissions.
        """
        from c2cgeoportal_commons.models.main import Metadata

        layer = metadatas_test_data["layer_wms"]
        layer.metadatas = [Metadata("_undefined", "This is an undefined metadata")]

        resp = self.get(test_app, f"layers_wms/{layer.id}")
        resp.form.submit("submit", status=302)

        metadata = layer.metadatas[0]
        assert metadata.name == "_undefined"
        assert metadata.value == "This is an undefined metadata"
