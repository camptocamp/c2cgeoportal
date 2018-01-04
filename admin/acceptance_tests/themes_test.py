# pylint: disable=no-self-use

import re
import pytest

from .treegroup_tests import TestTreeGroup


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def theme_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        Theme, Role, Functionality, LayergroupTreeitem, \
        Interface, Metadata, LayerGroup

    dbsession.begin_nested()

    interfaces = [Interface(name) for name in ['desktop', 'mobile', 'edit', 'routing']]

    groups = [LayerGroup(name='layer_group_{}'.format(i)) for i in range(0, 5)]

    functionalities = [Functionality(name=name, value='value_{}'.format(v))
                       for name in ('default_basemap', 'location') for v in range(0, 4)]

    roles = [Role('secretary_' + str(i)) for i in range(0, 4)]

    metadatas_protos = [('copyable', 'true'),
                        ('disclaimer', '© le momo'),
                        ('snappingConfig', '{"tolerance": 50}')]
    themes = []
    for i in range(0, 25):
        theme = Theme(name='theme_{}'.format(i),
                      ordering=1,
                      icon='icon_{}'.format(i))
        theme.public = 1 == i % 2
        theme.interfaces = [interfaces[i % 4],
                            interfaces[(i + 2) % 4]]

        theme.metadatas = [Metadata(name=metadatas_protos[id][0],
                                    value=metadatas_protos[id][1])
                           for id in [i % 3, (i + 2) % 3]]
        for metadata in theme.metadatas:
            metadata.item = theme

        theme.functionalities = [functionalities[i % 8], functionalities[(i + 3) % 8]]

        theme.restricted_roles = [roles[i % 4], roles[(i + 2) % 4]]

        dbsession.add(LayergroupTreeitem(group=groups[i % 5],
                                         item=theme,
                                         ordering=len(groups[i % 5].children_relation)))
        dbsession.add(LayergroupTreeitem(group=groups[(i + 3) % 5],
                                         item=theme,
                                         ordering=len(groups[(i + 3) % 5].children_relation)))

        dbsession.add(theme)
        themes.append(theme)

    yield {
        'themes': themes,
        'interfaces': interfaces,
        'groups': groups,
        'functionalities': functionalities,
        'roles': roles,
    }

    dbsession.rollback()


@pytest.mark.usefixtures('theme_test_data', 'transact', 'test_app')
class TestTheme(TestTreeGroup):

    _prefix = '/themes'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'Themes')

        expected = [('_id_', '', 'false'),
                    ('name', 'Name'),
                    ('metadata_url', 'Metadata URL'),
                    ('description', 'Description'),
                    ('ordering', 'Order'),
                    ('public', 'Public'),
                    ('icon', 'Icon'),
                    ('functionalities', 'Functionalities', 'false'),
                    ('restricted_roles', 'Roles', 'false'),
                    ('interfaces', 'Interfaces', 'false'),
                    ('parents_relation', 'Parents', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        self.check_grid_headers(resp, expected)

    def test_grid_complex_column_val(self, test_app, theme_test_data):
        first_row = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10
            },
            status=200
        ).json['rows'][0]

        first_theme = theme_test_data['themes'][0]

        assert first_theme.id == int(first_row['_id_'])
        assert first_theme.name == first_row['name']
        assert 'default_basemap=value_0, default_basemap=value_3' == first_row['functionalities']
        assert 'secretary_0, secretary_2' == first_row['restricted_roles']
        assert 'desktop, edit' == first_row['interfaces']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == first_row['metadatas']

    def test_grid_search(self, test_app):
        # search on metadatas key and value parts
        self.check_search(test_app, 'disclai ©', 16)

        # search on metadatas case insensitive
        self.check_search(test_app, 'disClaimer: © le momO', 16)

        # search on metadatas with no match
        self.check_search(test_app, 'DIfclaimer momo', 0)

        # search on interfaces
        self.check_search(test_app, 'routing', 12)

        # search on roles
        self.check_search(test_app, 'ary_2', 13)

        # search with underscores (wildcard)
        self.check_search(test_app, 'disclaimer m_m_', 16)

        # search on functionalities
        self.check_search(test_app, 'default_basemap value_0', 7)

    def test_public_checkbox_edit(self, test_app, theme_test_data):
        theme = theme_test_data['themes'][10]
        form10 = test_app.get('/themes/{}'.format(theme.id), status=200).form
        assert not form10['public'].checked
        theme = theme_test_data['themes'][11]
        form11 = test_app.get('/themes/{}'.format(theme.id), status=200).form
        assert form11['public'].checked

    def test_edit(self, test_app, theme_test_data, dbsession):
        theme = theme_test_data['themes'][0]

        resp = test_app.get('/themes/{}'.format(theme.id), status=200)
        form = resp.form

        assert str(theme.id) == self.get_first_field_named(form, 'id').value
        assert 'hidden' == self.get_first_field_named(form, 'id').attrs['type']
        assert theme.name == self.get_first_field_named(form, 'name').value
        assert str(theme.metadata_url or '') == form['metadata_url'].value
        assert str(theme.description or '') == self.get_first_field_named(form, 'description').value
        assert str(theme.ordering or '') == form['ordering'].value
        assert theme.public == form['public'].checked

        interfaces = theme_test_data['interfaces']
        assert set((interfaces[0].id, interfaces[2].id)) == set(i.id for i in theme.interfaces)
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in theme.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

        functionalities = theme_test_data['functionalities']
        assert set((
            functionalities[0].id,
            functionalities[3].id
        )) == set(f.id for f in theme.functionalities)
        self.check_checkboxes(
            form,
            'functionalities',
            [{
                'label': '{}={}'.format(f.name, f.value),
                'value': str(f.id),
                'checked': f in theme.functionalities
            } for f in sorted(functionalities, key=lambda f: (f.name, f.value))])

        self.check_children(
            form,
            'children_relation',
            [{
                'label': rel.treeitem.name,
                'values': {
                    'id': str(rel.id),
                    'treeitem_id': str(rel.treeitem.id)
                }
            } for rel in theme.children_relation]
        )

        new_values = {
            'name': 'new_name',
            'metadata_url': 'https://new_metadata_url',
            'description': 'new description',
            'ordering': 442,
            'public': True,
            'icon': 'static://img/cadastre.jpg'
        }
        for key, value in new_values.items():
            self.set_first_field_named(form, key, value)
        form['interfaces'] = [interfaces[1].id, interfaces[3].id]
        form['functionalities'] = [functionalities[2].id]
        form['restricted_roles'] = []

        resp = form.submit('submit')
        assert str(theme.id) == re.match('http://localhost/themes/(.*)', resp.location).group(1)

        dbsession.expire(theme)
        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(theme, key)
            else:
                assert str(value or '') == str(getattr(theme, key) or '')
        assert set([interfaces[1].id, interfaces[3].id]) == set(
            [interface.id for interface in theme.interfaces])
        assert set([functionalities[2].id]) == set(
            [functionality.id for functionality in theme.functionalities])
        assert 0 == len(theme.restricted_roles)

    def test_post_new_with_children_invalid(self, test_app, theme_test_data):
        """
        Check there is no rendering error when validation fails.
        """
        groups = theme_test_data['groups']
        resp = test_app.post(
            '{}/new'.format(self._prefix),
            (
                ('_charset_', 'UTF-8'),
                ('__formid__', 'deform'),
                ('id', ''),
                ('__start__', 'children_relation:sequence'),
                ('__start__', 'layergroup_treeitem:mapping'),
                ('id', ''),
                ('treeitem_id', groups[1].id),
                ('ordering', ''),
                ('__end__', 'layergroup_treeitem:mapping'),
                ('__end__', 'children_relation:sequence'),
                ('formsubmit', 'formsubmit')
            ),
            status=200)
        assert 'Required' == resp.html.select_one('.item-name .help-block').getText().strip()

    def test_post_new_with_children_success(self, test_app, dbsession, theme_test_data):
        groups = theme_test_data['groups']
        resp = test_app.post(
            '{}/new'.format(self._prefix),
            (
                ('_charset_', 'UTF-8'),
                ('__formid__', 'deform'),
                ('name', 'new_with_children'),
                ('metadata_url', ''),
                ('description', ''),
                ('ordering', '100'),
                ('id', ''),
                ('__start__', 'children_relation:sequence'),
                ('__start__', 'layergroup_treeitem:mapping'),
                ('id', ''),
                ('treeitem_id', groups[1].id),
                ('ordering', ''),
                ('__end__', 'layergroup_treeitem:mapping'),
                ('__start__', 'layergroup_treeitem:mapping'),
                ('id', ''),
                ('treeitem_id', groups[3].id),
                ('ordering', ''),
                ('__end__', 'layergroup_treeitem:mapping'),
                ('__start__', 'layergroup_treeitem:mapping'),
                ('id', ''),
                ('treeitem_id', groups[4].id),
                ('ordering', ''),
                ('__end__', 'layergroup_treeitem:mapping'),
                ('__end__', 'children_relation:sequence'),
                ('formsubmit', 'formsubmit')
            ),
            status=302)

        from c2cgeoportal_commons.models.main import Theme
        theme = dbsession.query(Theme). \
            filter(Theme.name == 'new_with_children'). \
            one()

        assert str(theme.id) == re.match('http://localhost/themes/(.*)', resp.location).group(1)

        assert (
            [groups[1].id, groups[3].id, groups[4].id] ==
            [rel.treeitem_id for rel in theme.children_relation]
        )
