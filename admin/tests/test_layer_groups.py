# pylint: disable=no-self-use

import re

import pytest

from .test_treegroup import TestTreeGroup


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def layer_groups_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import LayerGroup, LayergroupTreeitem, Metadata

    metadatas_protos = [
        ("copyable", "true"),
        ("disclaimer", "© le momo"),
        ("snappingConfig", '{"tolerance": 50}'),
    ]

    groups = []
    for i in range(0, 12):
        group = LayerGroup(name=f"groups_{i:02d}")
        group.metadatas = [
            Metadata(name=metadatas_protos[id][0], value=metadatas_protos[id][1])
            for id in [i % 3, (i + 2) % 3]
        ]
        for metadata in group.metadatas:
            metadata.item = group

        dbsession.add(group)
        groups.append(group)

    tree = {1: {2: {3, 4, 5}, 6: {4, 5}, 8: {7}, 9: {0, 10, 11}}}

    def add_relation(parent_idx, child_idx):
        dbsession.add(
            LayergroupTreeitem(
                group=groups[parent_idx], item=groups[child_idx], ordering=len(group.children_relation)
            )
        )

    def flatten_tree(key, value):
        if isinstance(value, set):
            for val in value:
                add_relation(key, val)
        else:
            for val in value.keys():
                add_relation(key, val)
                flatten_tree(val, value[val])

    flatten_tree(1, tree[1])

    dbsession.flush()

    yield {"groups": groups}


@pytest.mark.usefixtures("layer_groups_test_data", "test_app")
class TestLayersGroups(TestTreeGroup):
    _prefix = "/admin/layer_groups"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Layers groups")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name"),
            ("description", "Description"),
            ("parents_relation", "Parents", "false"),
            ("metadatas", "Metadatas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_groups_test_data):
        json = self.check_search(test_app, sort="name")

        row = json["rows"][4]
        group = layer_groups_test_data["groups"][4]

        assert group.id == int(row["_id_"])
        assert group.name == row["name"]
        assert "groups_02, groups_06" == row["parents_relation"]
        assert "disclaimer: © le momo, copyable: true" == row["metadatas"]

    def test_grid_search(self, test_app):
        # search on metadatas
        self.check_search(test_app, "copyable", total=8)

    def test_edit(self, test_app, layer_groups_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction

        group = layer_groups_test_data["groups"][1]

        form = self.get_item(test_app, group.id).form

        assert str(group.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert group.name == self.get_first_field_named(form, "name").value
        assert str(group.description or "") == self.get_first_field_named(form, "description").value

        self.check_children(
            form,
            "children_relation",
            [
                {
                    "label": rel.treeitem.name,
                    "values": {"id": str(rel.id), "treeitem_id": str(rel.treeitem.id)},
                }
                for rel in group.children_relation
            ],
        )

        new_values = {
            "name": "new_name",
            "description": "new description",
        }
        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)

        resp = form.submit("submit")
        assert str(group.id) == re.match(
            r"http://localhost/admin/layer_groups/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        dbsession.expire(group)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(group, key)
            else:
                assert str(value or "") == str(getattr(group, key) or "")

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "layergroup"
        assert log.element_id == group.id
        assert log.element_name == group.name
        assert log.username == "test_user"

    def test_post_new_with_children_invalid(self, test_app, layer_groups_test_data):
        """
        Check there is no rendering error when validation fails.
        """
        groups = layer_groups_test_data["groups"]
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
        assert "Required" == resp.html.select_one(".item-name .help-block").getText().strip()

    def test_post_new_with_children_success(self, test_app, dbsession, layer_groups_test_data):
        from c2cgeoportal_commons.models.main import Log, LogAction

        groups = layer_groups_test_data["groups"]
        resp = test_app.post(
            f"{self._prefix}/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("name", "new_with_children"),
                ("description", ""),
                ("id", ""),
                ("__start__", "children_relation:sequence"),
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
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", groups[5].id),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__end__", "children_relation:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        from c2cgeoportal_commons.models.main import LayerGroup

        group = dbsession.query(LayerGroup).filter(LayerGroup.name == "new_with_children").one()

        assert str(group.id) == re.match(
            r"http://localhost/admin/layer_groups/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        assert [groups[3].id, groups[4].id, groups[5].id] == [
            rel.treeitem_id for rel in group.children_relation
        ]

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "layergroup"
        assert log.element_id == group.id
        assert log.element_name == group.name
        assert log.username == "test_user"

    def test_post_with_ancestor(self, layer_groups_test_data, test_app):
        """
        Check that ancestors are refused to avoid cycles.
        """
        groups = layer_groups_test_data["groups"]
        resp = test_app.post(
            f"{self._prefix}/{groups[3].id}",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("id", str(groups[3].id)),
                ("name", groups[3].name),
                ("__start__", "children_relation:sequence"),
                ("__start__", "layergroup_treeitem:mapping"),
                ("id", ""),
                ("treeitem_id", str(groups[1].id)),
                ("ordering", ""),
                ("__end__", "layergroup_treeitem:mapping"),
                ("__end__", "children_relation:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=200,
        )
        assert (
            f"Value {groups[1].id} does not exist in table treeitem or is not allowed to avoid cycles"
            == resp.html.select_one(".item-children_relation + .help-block").getText().strip()
        )

    def test_duplicate(self, layer_groups_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LayerGroup

        group = layer_groups_test_data["groups"][1]

        resp = test_app.get(f"{self._prefix}/{group.id}/duplicate", status=200)
        form = resp.form

        group = dbsession.query(LayerGroup).filter(LayerGroup.id == group.id).one()

        assert "" == self.get_first_field_named(form, "id").value
        assert group.name == self.get_first_field_named(form, "name").value
        assert str(group.description or "") == self.get_first_field_named(form, "description").value

        self.check_children(
            form,
            "children_relation",
            [
                {"label": rel.treeitem.name, "values": {"id": "", "treeitem_id": str(rel.treeitem.id)}}
                for rel in group.children_relation
            ],
        )

        self.set_first_field_named(form, "name", "duplicated")
        resp = form.submit("submit")

        duplicated = dbsession.query(LayerGroup).filter(LayerGroup.name == "duplicated").one()

        assert str(duplicated.id) == re.match(
            rf"http://localhost{self._prefix}/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert duplicated.id != group.id
        assert duplicated.children_relation[0].id != group.children_relation[0].id
        assert duplicated.children_relation[0].treeitem.id == group.children_relation[0].treeitem.id

    def test_unicity_validator(self, layer_groups_test_data, test_app):
        group = layer_groups_test_data["groups"][1]
        resp = test_app.get(f"{self._prefix}/{group.id}/duplicate", status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{group.name} is already used.")

    def test_delete(self, test_app, dbsession, layer_groups_test_data):
        from c2cgeoportal_commons.models.main import (
            LayerGroup,
            LayergroupTreeitem,
            Log,
            LogAction,
            TreeGroup,
            TreeItem,
        )

        group = layer_groups_test_data["groups"][9]

        assert (
            3
            == dbsession.query(LayergroupTreeitem).filter(LayergroupTreeitem.treegroup_id == group.id).count()
        )

        assert (
            1
            == dbsession.query(LayergroupTreeitem).filter(LayergroupTreeitem.treeitem_id == group.id).count()
        )

        test_app.delete(f"/admin/layer_groups/{group.id}", status=200)

        dbsession.expire_all()

        assert dbsession.query(LayerGroup).get(group.id) is None
        assert dbsession.query(TreeGroup).get(group.id) is None
        assert dbsession.query(TreeItem).get(group.id) is None

        assert (
            0
            == dbsession.query(LayergroupTreeitem).filter(LayergroupTreeitem.treegroup_id == group.id).count()
        )

        assert (
            0
            == dbsession.query(LayergroupTreeitem).filter(LayergroupTreeitem.treeitem_id == group.id).count()
        )

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "layergroup"
        assert log.element_id == group.id
        assert log.element_name == group.name
        assert log.username == "test_user"
