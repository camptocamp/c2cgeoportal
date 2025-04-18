# pylint: disable=no-self-use

import re

import pytest

from .test_treegroup import TestTreeGroup


@pytest.fixture
def theme_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import (
        Functionality,
        Interface,
        LayerGroup,
        LayergroupTreeitem,
        LayerWMS,
        Metadata,
        OGCServer,
        Role,
        Theme,
    )

    interfaces = [Interface(name) for name in ["desktop", "mobile", "edit", "routing"]]
    dbsession.add_all(interfaces)

    groups = [LayerGroup(name=f"layer_group_{i}") for i in range(5)]
    dbsession.add_all(groups)

    layer = LayerWMS(name="layer_wms")
    layer.ogc_server = OGCServer(name="server")
    layers = [layer]
    dbsession.add_all(layers)

    # Note that "default_theme" is not relevant for themes
    functionalities = [
        Functionality(name=name, value=f"value_{v}")
        for name in ("default_basemap", "default_theme")
        for v in range(4)
    ]
    dbsession.add_all(functionalities)

    roles = [Role("secretary_" + str(i)) for i in range(4)]
    dbsession.add_all(roles)

    metadatas_protos = [
        ("copyable", "true"),
        ("disclaimer", "© le momo"),
        ("snappingConfig", '{"tolerance": 50}'),
    ]
    themes = []
    for i in range(25):
        theme = Theme(name=f"theme_{i}", ordering=1, icon=f"icon_{i}")
        theme.public = i % 2 == 1
        theme.interfaces = [interfaces[i % 4], interfaces[(i + 2) % 4]]
        theme.metadatas = [
            Metadata(name=metadatas_protos[id][0], value=metadatas_protos[id][1])
            for id in [i % 3, (i + 2) % 3]
        ]
        for metadata in theme.metadatas:
            metadata.item = theme
        theme.functionalities = [functionalities[i % 4]]
        theme.restricted_roles = [roles[i % 4], roles[(i + 2) % 4]]

        dbsession.add(
            LayergroupTreeitem(
                group=theme,
                item=groups[i % 5],
                ordering=len(groups[i % 5].children_relation),
            ),
        )
        dbsession.add(
            LayergroupTreeitem(
                group=theme,
                item=groups[(i + 3) % 5],
                ordering=len(groups[(i + 3) % 5].children_relation),
            ),
        )

        dbsession.add(theme)
        themes.append(theme)

    dbsession.flush()

    return {
        "themes": themes,
        "interfaces": interfaces,
        "groups": groups,
        "layers": layers,
        "functionalities": functionalities,
        "roles": roles,
    }


@pytest.mark.usefixtures("theme_test_data", "test_app")
class TestTheme(TestTreeGroup):
    _prefix = "/admin/themes"

    def test_index_rendering(self, test_app) -> None:
        resp = self.get(test_app)

        self.check_left_menu(resp, "Themes")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name"),
            ("description", "Description"),
            ("ordering", "Order"),
            ("public", "Public"),
            ("icon", "Icon"),
            ("functionalities", "Functionalities", "false"),
            ("restricted_roles", "Roles", "false"),
            ("interfaces", "Interfaces", "false"),
            ("metadatas", "Metadatas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, theme_test_data) -> None:
        json = self.check_search(test_app)

        first_row = json["rows"][0]
        first_theme = theme_test_data["themes"][0]

        assert first_theme.id == int(first_row["_id_"])
        assert first_theme.name == first_row["name"]
        assert first_row["functionalities"] == "default_basemap=value_0"
        assert first_row["restricted_roles"] == "secretary_0, secretary_2"
        assert first_row["interfaces"] == "desktop, edit"
        assert first_row["metadatas"] == 'copyable: true, snappingConfig: {"tolerance": 50}'

    def test_grid_search(self, test_app) -> None:
        # search on metadatas key and value parts
        self.check_search(test_app, "disclai ©", total=16)

        # search on metadatas case insensitive
        self.check_search(test_app, "disClaimer: © le momO", total=16)

        # search on metadatas with no match
        self.check_search(test_app, "DIfclaimer momo", total=0)

        # search on interfaces
        self.check_search(test_app, "routing", total=12)

        # search on roles
        self.check_search(test_app, "ary_2", total=13)

        # search with underscores (wildcard)
        self.check_search(test_app, "disclaimer m_m_", total=16)

        # search on functionalities
        self.check_search(test_app, "default_basemap value_0", total=7)

    def test_public_checkbox_edit(self, test_app, theme_test_data) -> None:
        theme = theme_test_data["themes"][10]
        form10 = test_app.get(f"/admin/themes/{theme.id}", status=200).form
        assert not form10["public"].checked
        theme = theme_test_data["themes"][11]
        form11 = test_app.get(f"/admin/themes/{theme.id}", status=200).form
        assert form11["public"].checked

    def test_edit(self, test_app, theme_test_data, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Log, LogAction

        theme = theme_test_data["themes"][0]

        resp = test_app.get(f"/admin/themes/{theme.id}", status=200)
        form = resp.form

        assert str(theme.id) == self.get_first_field_named(form, "id").value
        assert self.get_first_field_named(form, "id").attrs["type"] == "hidden"
        assert theme.name == self.get_first_field_named(form, "name").value
        assert str(theme.description or "") == self.get_first_field_named(form, "description").value
        assert str(theme.ordering or "") == self.get_first_field_named(form, "ordering").value
        assert theme.public == form["public"].checked

        interfaces = theme_test_data["interfaces"]
        assert {interfaces[0].id, interfaces[2].id} == {i.id for i in theme.interfaces}
        self._check_interfaces(form, interfaces, theme)

        functionalities = theme_test_data["functionalities"]
        assert {functionalities[0].id} == {f.id for f in theme.functionalities}
        self.check_checkboxes(
            form,
            "functionalities",
            [
                {
                    "label": f"{f.name}={f.value}",
                    "value": str(f.id),
                    "checked": f in theme.functionalities,
                }
                for f in sorted(
                    [f for f in functionalities if f.name in ("default_basemap")],
                    key=lambda f: (f.name, f.value),
                )
            ],
        )

        self.check_children(
            form,
            "children_relation",
            [
                {
                    "label": rel.treeitem.name,
                    "values": {"id": str(rel.id), "treeitem_id": str(rel.treeitem.id)},
                }
                for rel in theme.children_relation
            ],
        )

        new_values = {
            "name": "new_name",
            "description": "new description",
            "ordering": 442,
            "public": True,
            "icon": "static://img/cadastre.jpg",
        }
        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)
        form["interfaces"] = [interfaces[1].id, interfaces[3].id]
        form["functionalities"] = [functionalities[2].id]
        form["restricted_roles"] = []

        resp = form.submit("submit")
        assert str(theme.id) == re.match(
            r"http://localhost/admin/themes/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        dbsession.expire(theme)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(theme, key)
            else:
                assert str(value or "") == str(getattr(theme, key) or "")
        assert {interfaces[1].id, interfaces[3].id} == {interface.id for interface in theme.interfaces}
        assert {functionalities[2].id} == {functionality.id for functionality in theme.functionalities}
        assert len(theme.restricted_roles) == 0

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "theme"
        assert log.element_id == theme.id
        assert log.element_name == theme.name
        assert log.username == "test_user"

    def test_post_new_with_children_invalid(self, test_app, theme_test_data) -> None:
        """Check there is no rendering error when validation fails."""
        groups = theme_test_data["groups"]
        resp = test_app.post(
            f"{self._prefix}/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("id", ""),
                ("__start__", "children_relation:sequence"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", groups[1].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__end__", "children_relation:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=200,
        )

        self._check_submission_problem(resp, "Required")

    def test_post_new_with_children_success(self, test_app, dbsession, theme_test_data) -> None:
        from c2cgeoportal_commons.models.main import Log, LogAction

        groups = theme_test_data["groups"]
        resp = test_app.post(
            f"{self._prefix}/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("name", "new_with_children"),
                ("description", ""),
                ("ordering", "100"),
                ("id", ""),
                ("__start__", "children_relation:sequence"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", groups[1].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", groups[3].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", groups[4].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__end__", "children_relation:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        from c2cgeoportal_commons.models.main import Theme

        theme = dbsession.query(Theme).filter(Theme.name == "new_with_children").one()

        assert str(theme.id) == re.match(
            r"http://localhost/admin/themes/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)

        assert [groups[1].id, groups[3].id, groups[4].id] == [
            rel.treeitem_id for rel in theme.children_relation
        ]

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.INSERT
        assert log.element_type == "theme"
        assert log.element_id == theme.id
        assert log.element_name == theme.name
        assert log.username == "test_user"

    def test_post_new_with_child_layer(self, theme_test_data, test_app) -> None:
        """Check layers are rejected by the validator (also means that they are not proposed to the user)."""
        layers = theme_test_data["layers"]
        resp = test_app.post(
            f"{self._prefix}/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("name", "new_with_child_layer"),
                ("description", ""),
                ("ordering", "100"),
                ("id", ""),
                ("__start__", "children_relation:sequence"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", layers[0].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__end__", "children_relation:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=200,
        )
        assert (
            f"Value {layers[0].id} does not exist in table treeitem or is not allowed to avoid cycles"
            == resp.html.select_one(".item-children_relation + .help-block").getText().strip()
        )

    def test_duplicate(self, theme_test_data, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Theme

        theme = theme_test_data["themes"][1]

        resp = test_app.get(f"{self._prefix}/{theme.id}/duplicate", status=200)
        form = resp.form

        assert self.get_first_field_named(form, "id").value == ""
        assert self.get_first_field_named(form, "id").attrs["type"] == "hidden"
        assert theme.name == self.get_first_field_named(form, "name").value
        assert str(theme.description or "") == self.get_first_field_named(form, "description").value
        assert str(theme.ordering or "") == self.get_first_field_named(form, "ordering").value

        assert theme.public == form["public"].checked

        interfaces = theme_test_data["interfaces"]
        assert {interfaces[1].id, interfaces[3].id} == {i.id for i in theme.interfaces}

        self._check_interfaces(form, interfaces, theme)

        functionalities = theme_test_data["functionalities"]
        assert {functionalities[1].id} == {f.id for f in theme.functionalities}
        self.check_checkboxes(
            form,
            "functionalities",
            [
                {
                    "label": f"{f.name}={f.value}",
                    "value": str(f.id),
                    "checked": f in theme.functionalities,
                }
                for f in sorted(
                    [f for f in functionalities if f.name in ("default_basemap")],
                    key=lambda f: (f.name, f.value),
                )
            ],
        )

        theme = dbsession.query(Theme).filter(Theme.id == theme.id).one()

        self.check_children(
            form,
            "children_relation",
            [
                {"label": rel.treeitem.name, "values": {"id": "", "treeitem_id": str(rel.treeitem.id)}}
                for rel in theme.children_relation
            ],
        )

        self.set_first_field_named(form, "name", "duplicated")
        resp = form.submit("submit")

        duplicated = dbsession.query(Theme).filter(Theme.name == "duplicated").one()

        assert str(duplicated.id) == re.match(
            rf"http://localhost{self._prefix}/(.*)\?msg_col=submit_ok",
            resp.location,
        ).group(1)
        assert duplicated.id != theme.id
        assert duplicated.children_relation[0].id != theme.children_relation[0].id
        assert duplicated.children_relation[0].treeitem.id == theme.children_relation[0].treeitem.id

    def test_delete(self, test_app, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Log, LogAction, Theme

        theme = dbsession.query(Theme).first()
        test_app.delete(f"/admin/themes/{theme.id}", status=200)
        assert dbsession.query(Theme).get(theme.id) is None

        log = dbsession.query(Log).one()
        assert log.date is not None
        assert log.action == LogAction.DELETE
        assert log.element_type == "theme"
        assert log.element_id == theme.id
        assert log.element_name == theme.name
        assert log.username == "test_user"

    def test_unicity_validator(self, theme_test_data, test_app) -> None:
        theme = theme_test_data["themes"][1]
        resp = test_app.get(f"{self._prefix}/{theme.id}/duplicate", status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{theme.name} is already used.")
