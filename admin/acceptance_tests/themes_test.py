# pylint: disable=no-self-use

import re
import pytest

from . import check_grid_headers


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
        'functionalities': functionalities,
        'roles': roles,
    }

    dbsession.rollback()


@pytest.mark.usefixtures('theme_test_data', 'transact', 'test_app')
class TestTheme():

    def test_view_index_rendering_in_app(self, test_app):
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
                    ('metadatas', 'Metadatas', 'false')]
        check_grid_headers(test_app, '/themes/', expected)

    def test_left_menu(self, test_app):
        html = test_app.get('/themes/', status=200).html
        main_menu = html.select_one('a[href="http://localhost/themes/"]').getText()
        assert 'Themes' == main_menu

    def test_grid_complex_column_val(self, test_app, theme_test_data):
        first_row = test_app.post('/themes/grid.json',
                                  params={'current': 1, 'rowCount': 10},
                                  status=200
                                  ).json['rows'][0]

        firsrt_theme = theme_test_data['themes'][0]

        assert firsrt_theme.id == int(first_row['_id_'])
        assert firsrt_theme.name == first_row['name']
        assert 'default_basemap=value_0, default_basemap=value_3' == first_row['functionalities']
        assert 'secretary_0, secretary_2' == first_row['restricted_roles']
        assert 'desktop, edit' == first_row['interfaces']
        assert 'copyable: true, snappingConfig: {"tolerance": 50}' == first_row['metadatas']

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

        assert str(theme.id) == form['id'].value
        assert 'hidden' == form['id'].attrs['type']
        assert theme.name == form['name'].value
        assert str(theme.metadata_url or '') == form['metadata_url'].value
        assert str(theme.description or '') == form['description'].value
        assert str(theme.ordering or '') == form['ordering'].value
        assert theme.public == form['public'].checked

        interfaces = theme_test_data['interfaces']
        functionalities = theme_test_data['functionalities']
        assert [interfaces[0].id, interfaces[2].id] == [interface.id for interface in theme.interfaces]
        for i, interface in enumerate(sorted(interfaces, key=lambda interface: interface.name)):
            field = form.get('interfaces', index=i)
            checkbox = form.html.select_one('#{}'.format(field.id))
            label = form.html.select_one('label[for={}]'.format(field.id))
            assert interface.name == list(label.stripped_strings)[0]
            assert str(interface.id) == checkbox['value']
            assert (interface in theme.interfaces) == field.checked

        new_values = {
            'name': 'new_name',
            'metadata_url': 'https://new_metadata_url',
            'description': 'new description',
            'ordering': 442,
            'public': True,
            'icon': 'static://img/cadastre.jpg'
        }
        for key, value in new_values.items():
            form[key] = value
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

    def test_grid_filter_on_metadatas_key_value_formatted(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'disClaimer: © le momO'
            },
            status=200
        ).json
        assert 16 == json['total']

    def test_grid_filter_on_metadatas_key_value_parts_not_formatted(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'disclai ©'
            },
            status=200
        ).json
        assert 16 == json['total']

    def test_grid_filter_on_metadatas_value_dont_match(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'DIfclaimer momo'
            },
            status=200
        ).json
        assert 0 == json['total']

    def test_grid_filter_on_interfaces(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'routing'
            },
            status=200
        ).json
        assert 12 == json['total']

    def test_grid_filter_on_role(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'ary_2'
            },
            status=200
        ).json
        assert 13 == json['total']

    def test_grid_filter_underscore_count_as_wildcard(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'disclaimer m_m_'
            },
            status=200
        ).json
        assert 16 == json['total']

    def test_grid_filter_functionnalities(self, test_app):
        json = test_app.post(
            '/themes/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': 'default_basemap value_0'
            },
            status=200
        ).json
        assert 7 == json['total']
