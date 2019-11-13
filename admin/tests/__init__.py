# pylint: disable=no-self-use

import os
import pprint

import pytest

skip_if_ci = pytest.mark.skipif(os.environ.get("CI", "false") == "true", reason="Not running on CI")


def get_test_default_layers(dbsession, default_ogc_server):
    from c2cgeoportal_commons.models.main import LayerWMTS, LayerWMS, LayerVectorTiles

    default_wms = LayerWMS("wms-defaults")
    default_wms.ogc_server = default_ogc_server
    default_wms.time_widget = "datepicker"
    default_wms.time_mode = "value"
    dbsession.add(default_wms)
    default_wmts = LayerWMTS("wmts-defaults")
    default_wmts.url = "https:///wmts.geo.admin_default.ch.org?service=wms&request=GetCapabilities"
    default_wmts.layer = "default"
    default_wmts.matrix_set = "matrix"
    dbsession.add(default_wmts)
    default_vectortiles = LayerVectorTiles("vectortiles-defaults")
    default_vectortiles.style = "https://vectortiles-staging.geoportail.lu/styles/roadmap/style.json"
    dbsession.add(default_vectortiles)
    dbsession.flush()
    return {"wms": default_wms, "wmts": default_wmts, "vectortiles": default_vectortiles}


def factory_build_layers(layer_builder, dbsession, add_dimension=True):
    from c2cgeoportal_commons.models.main import (
        RestrictionArea,
        LayergroupTreeitem,
        Interface,
        Dimension,
        Metadata,
        LayerGroup,
    )

    restrictionareas = [RestrictionArea(name="restrictionarea_{}".format(i)) for i in range(0, 5)]

    interfaces = [Interface(name) for name in ["desktop", "mobile", "edit", "routing"]]

    dimensions_protos = [("Date", "2017"), ("Date", "2018"), ("Date", "1988"), ("CLC", "all")]

    metadatas_protos = [
        ("copyable", "true"),
        ("disclaimer", "© le momo"),
        ("snappingConfig", '{"tolerance": 50}'),
    ]

    groups = [LayerGroup(name="layer_group_{}".format(i)) for i in range(0, 5)]

    layers = []
    for i in range(0, 25):

        layer = layer_builder(i)

        if add_dimension:
            layer.dimensions = [
                Dimension(name=dimensions_protos[id][0], value=dimensions_protos[id][1], layer=layer)
                for id in [i % 3, (i + 2) % 4, (i + 3) % 4]
            ]

        layer.metadatas = [
            Metadata(name=metadatas_protos[id][0], value=metadatas_protos[id][1])
            for id in [i % 3, (i + 2) % 3]
        ]
        for metadata in layer.metadatas:
            metadata.item = layer

        if i % 10 != 1:
            layer.interfaces = [interfaces[i % 4], interfaces[(i + 2) % 4]]

        layer.restrictionareas = [restrictionareas[i % 5], restrictionareas[(i + 2) % 5]]

        dbsession.add(
            LayergroupTreeitem(group=groups[i % 5], item=layer, ordering=len(groups[i % 5].children_relation))
        )
        dbsession.add(
            LayergroupTreeitem(
                group=groups[(i + 3) % 5], item=layer, ordering=len(groups[(i + 3) % 5].children_relation)
            )
        )

        dbsession.add(layer)
        layers.append(layer)
    return {"restrictionareas": restrictionareas, "layers": layers, "interfaces": interfaces}


class AbstractViewsTests:

    _prefix = None  # url prefix (index view url). Example : /users

    def get(self, test_app, path="", locale="en", status=200, **kwargs):
        return test_app.get(
            "{}{}".format(self._prefix, path),
            headers={"Cookie": "_LOCALE_={}".format(locale)},
            status=status,
            **kwargs,
        )

    def get_item(self, test_app, item_id, **kwargs):
        return self.get(test_app, "/{}".format(item_id), **kwargs)

    def check_left_menu(self, resp, title):
        link = resp.html.select_one(".navbar li.active a")
        assert "http://localhost{}".format(self._prefix) == link.attrs["href"]
        assert title == link.getText()

    def check_grid_headers(self, resp, expected_col_headers):
        pp = pprint.PrettyPrinter(indent=4)
        effective_cols = [
            (th.attrs["data-field"], th.getText(), th.attrs["data-sortable"]) for th in resp.html.select("th")
        ]
        expected_col_headers = [(x[0], x[1], len(x) == 3 and x[2] or "true") for x in expected_col_headers]
        assert expected_col_headers == effective_cols, str.format(
            "\n\n{}\n\n differs from \n\n{}", pp.pformat(expected_col_headers), pp.pformat(effective_cols)
        )
        actions = resp.html.select_one('th[data-field="actions"]')
        assert "false" == actions.attrs["data-sortable"]
        assert 1 == len(list(filter(lambda x: next(x.stripped_strings) == "New", resp.html.findAll("a"))))

    def check_search(self, test_app, search="", offset=0, limit=10, sort="", order="", total=None):
        json = test_app.post(
            "{}/grid.json".format(self._prefix),
            params={"offset": offset, "limit": limit, "search": search, "sort": sort, "order": order},
            status=200,
        ).json
        if total is not None:
            assert total == json["total"]
        return json

    def check_checkboxes(self, form, name, expected):
        for i, exp in enumerate(expected):
            field = form.get(name, index=i)
            checkbox = form.html.select_one("#{}".format(field.id))
            label = form.html.select_one("label[for={}]".format(field.id))
            assert exp["label"] == list(label.stripped_strings)[0]
            assert exp["value"] == checkbox["value"]
            assert exp["checked"] == field.checked

    def _check_interfaces(self, form, interfaces, item):
        self.check_checkboxes(
            form,
            "interfaces",
            [
                {"label": i.name, "value": str(i.id), "checked": i in item.interfaces}
                for i in sorted(interfaces, key=lambda i: i.name)
            ],
        )

    def _check_restrictionsareas(self, form, ras, item):
        self.check_checkboxes(
            form,
            "restrictionareas",
            [
                {"label": ra.name, "value": str(ra.id), "checked": ra in item.restrictionareas}
                for ra in sorted(ras, key=lambda ra: ra.name)
            ],
        )

    def _check_roles(self, form, roles, item):
        self.check_checkboxes(
            form,
            "roles",
            [
                {"label": role.name, "value": str(role.id), "checked": role in item.roles}
                for role in sorted(roles, key=lambda role: role.name)
            ],
        )

    def get_first_field_named(self, form, name):
        return form.fields.get(name)[0]

    def set_first_field_named(self, form, name, value):
        form.fields.get(name)[0].value__set(value)

    def _check_sequence(self, sequence, expected):
        seq_items = sequence.select(".deform-seq-item")
        assert len(expected) == len(seq_items)
        for seq_item, exp in zip(seq_items, expected):
            self._check_mapping(seq_item, exp)

    def _check_mapping(self, mapping_item, expected):
        for exp in expected:
            input_tag = mapping_item.select_one('[name="{}"]'.format(exp["name"]))
            if "value" in exp:
                if input_tag.name == "select":
                    self._check_select(input_tag, exp["value"])
                elif input_tag.name == "textarea":
                    assert (exp["value"] or "") == (input_tag.string or "")
                else:
                    assert (exp["value"] or "") == input_tag.attrs.get("value", "")
            if exp.get("hidden", False):
                assert "hidden" == input_tag["type"]
            if "label" in exp:
                label_tag = mapping_item.select_one('label[for="{}"]'.format(input_tag["id"]))
                assert exp["label"] == label_tag.getText().strip()

    def _check_select(self, select, expected):
        for exp, option in zip(expected, select.find_all("option")):
            if "text" in exp:
                assert exp["text"] == option.text
            if "value" in exp:
                assert exp["value"] == option["value"]
            if "selected" in exp:
                assert exp["selected"] == ("selected" in option.attrs)

    def _check_submission_problem(self, resp, expected_msg):
        assert (
            "There was a problem with your submission"
            == resp.html.select_one('div[class="error-msg-lbl"]').text
        )
        assert (
            "Errors have been highlighted below" == resp.html.select_one('div[class="error-msg-detail"]').text
        )
        assert (
            expected_msg
            == resp.html.select_one("[class~='has-error']")
            .select_one("[class~='help-block']")
            .getText()
            .strip()
        )

    def _check_dimensions(self, html, dimensions, duplicated=False):
        item = html.select_one(".item-dimensions")
        self._check_sequence(
            item,
            [
                [
                    {"name": "id", "value": "" if duplicated else str(d.id), "hidden": True},
                    {"name": "name", "value": d.name, "label": "Name"},
                    {"name": "value", "value": d.value, "label": "Value"},
                    {"name": "description", "value": d.description, "label": "Description"},
                ]
                for d in sorted(dimensions, key=lambda d: d.name)
            ],
        )
