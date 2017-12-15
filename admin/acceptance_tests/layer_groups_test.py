# pylint: disable=no-self-use

import re
import pytest

from . import AbstractViewsTests


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def layer_groups_test_data(dbsession):
    from c2cgeoportal_commons.models.main import LayerGroup, Metadata, LayergroupTreeitem

    dbsession.begin_nested()

    metadatas_protos = [("copyable", "true"),
                        ("disclaimer", "© le momo"),
                        ("snappingConfig", '{"tolerance": 50}')]

    groups = []
    for i in range(0, 12):
        group = LayerGroup(
            name='groups_{num:02d}'.format(num=i),
            is_expanded=False,
            is_internal_wms=True,
            is_base_layer=False)
        group.metadatas = [Metadata(name=metadatas_protos[id][0],
                                    value=metadatas_protos[id][1])
                           for id in [i % 3, (i + 2) % 3]]
        for metadata in group.metadatas:
            metadata.item = group

        dbsession.add(group)
        groups.append(group)

    tree = {1: {2: {3, 4, 5}, 6: {4, 5}, 8: {7}, 9: {0, 10, 11}}}

    def add_relation(parent_idx, child_idx):
        dbsession.add(LayergroupTreeitem(group=groups[parent_idx],
                                         item=groups[child_idx],
                                         ordering=len(group.children_relation)))

    def flatten_tree(key, value):
        if isinstance(value, set):
            for val in value:
                add_relation(key, val)
        else:
            for val in value.keys():
                add_relation(key, val)
                flatten_tree(val, value[val])

    flatten_tree(1, tree[1])

    yield {
        "groups": groups
    }

    dbsession.rollback()


@pytest.mark.usefixtures('layer_groups_test_data', 'transact', 'test_app')
class TestLayersGroups(AbstractViewsTests):

    _prefix = '/layer_groups'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'Layers groups')

        expected = [('_id_', '', 'false'),
                    ('name', 'Name'),
                    ('metadata_url', 'Metadata URL'),
                    ('description', 'Description'),
                    ('is_expanded', 'Expanded'),
                    ('is_internal_wms', 'Internal WMS'),
                    ('is_base_layer', 'Base layers group'),
                    ('parents_relation', 'Parents', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, layer_groups_test_data):
        json = test_app.post(
            "/layer_groups/grid.json",
            params={
                "current": 1,
                "rowCount": 10,
                "sort[name]": "asc"
            },
            status=200
        ).json
        row = json["rows"][4]

        group = layer_groups_test_data['groups'][4]

        assert group.id == int(row["_id_"])
        assert group.name == row["name"]
        assert 'groups_02, groups_06' == row['parents_relation']
        assert 'disclaimer: © le momo, copyable: true' == row['metadatas']

    @pytest.mark.skip(reason="use value to be defined")
    def test_grid_filter_on_parents(self, test_app):
        json = test_app.post(
            '/layer_groups/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'groups_11'
            },
            status=200
        ).json
        assert 4 == json['total']

    def test_grid_search(self, test_app):
        # search on metadatas
        self.check_search(test_app, 'copyable', 8)

    def test_edit(self, test_app, layer_groups_test_data, dbsession):
        group = layer_groups_test_data['groups'][1]

        form = self.get_item(test_app, group.id).form

        assert str(group.id) == self.getFirstFieldNamed(form, 'id').value
        assert 'hidden' == self.getFirstFieldNamed(form, 'id').attrs['type']
        assert group.name == self.getFirstFieldNamed(form, 'name').value
        assert str(group.metadata_url or '') == form['metadata_url'].value
        assert str(group.description or '') == self.getFirstFieldNamed(form, 'description').value
        assert group.is_expanded is False
        assert group.is_expanded == form['is_expanded'].checked
        assert group.is_internal_wms is True
        assert group.is_internal_wms == form['is_internal_wms'].checked
        assert group.is_base_layer is False
        assert group.is_base_layer == form['is_base_layer'].checked

        new_values = {
            'name': 'new_name',
            'metadata_url': 'https://new_metadata_url',
            'description': 'new description',
            'is_expanded': True,
            'is_internal_wms': False,
            'is_base_layer': True
        }
        for key, value in new_values.items():
            self.setFirstFieldNamed(form, key, value)

        resp = form.submit("submit")
        assert str(group.id) == re.match('http://localhost/layer_groups/(.*)', resp.location).group(1)

        dbsession.expire(group)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(group, key)
            else:
                assert str(value or '') == str(getattr(group, key) or '')

    def test_delete(self, test_app, dbsession, layer_groups_test_data):
        from c2cgeoportal_commons.models.main import LayerGroup, TreeGroup, TreeItem, LayergroupTreeitem

        group_id = layer_groups_test_data['groups'][9].id

        assert 3 == dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treegroup_id == group_id). \
            count()

        assert 1 == dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treeitem_id == group_id). \
            count()

        test_app.delete("/layer_groups/{}".format(group_id), status=200)

        dbsession.expire_all()

        assert dbsession.query(LayerGroup).get(group_id) is None
        assert dbsession.query(TreeGroup).get(group_id) is None
        assert dbsession.query(TreeItem).get(group_id) is None

        assert 0 == dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treegroup_id == group_id). \
            count()

        assert 0 == dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treeitem_id == group_id). \
            count()
