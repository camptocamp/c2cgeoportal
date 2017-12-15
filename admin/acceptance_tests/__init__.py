# pylint: disable=no-self-use

import os
import pprint
import pytest

skip_if_ci = pytest.mark.skipif(
    os.environ.get('CI', "false") == "true", reason="Not running on CI"
)


class AbstractViewsTests():

    _prefix = None  # url prefix (index view url). Example : /users

    def get(self, test_app, path='', locale='en', status=200, **kwargs):
        return test_app.get(
            '{}{}'.format(self._prefix, path),
            headers={
                'Cookie': '_LOCALE_={}'.format(locale)
            },
            status=status,
            **kwargs)

    def get_item(self, test_app, item_id, **kwargs):
        return self.get(test_app, '/{}'.format(item_id), **kwargs)

    def check_left_menu(self, resp, title):
        link = resp.html.select_one('#main-menu li.active a')
        assert 'http://localhost{}'.format(self._prefix) == link.attrs['href']
        assert title == link.getText()

    def check_grid_headers(self, resp, expected_col_headers):
        pp = pprint.PrettyPrinter(indent=4)
        effective_cols = [(th.attrs['data-column-id'], th.getText(), th.attrs['data-sortable'])
                          for th in resp.html.select('th')]
        expected_col_headers = [(x[0], x[1], len(x) == 3 and x[2] or 'true') for x in expected_col_headers]
        assert expected_col_headers == effective_cols, \
            str.format('\n\n{}\n\n differs from \n\n{}',
                       pp.pformat(expected_col_headers),
                       pp.pformat(effective_cols))
        commands = resp.html.select_one('th[data-column-id="_id_"]')
        assert 'false' == commands.attrs['data-searchable']
        assert 'false' == commands.attrs['data-sortable']
        assert 1 == len(list(filter(lambda x: str(x.contents) == "['New']",
                                    resp.html.findAll('a'))))

    def check_search(self, test_app, search, total):
        json = test_app.post(
            '{}/grid.json'.format(self._prefix),
            params={
                'current': 1,
                'rowCount': 10,
                'searchPhrase': search
            },
            status=200
        ).json
        assert total == json['total']

    def check_checkboxes(self, form, name, expected):
        for i, exp in enumerate(expected):
            field = form.get(name, index=i)
            checkbox = form.html.select_one('#{}'.format(field.id))
            label = form.html.select_one('label[for={}]'.format(field.id))
            assert exp['label'] == list(label.stripped_strings)[0]
            assert exp['value'] == checkbox['value']
            assert exp['checked'] == field.checked

    def getFirstFieldNamed(self, form, name):
        return form.fields.get(name)[0]

    def setFirstFieldNamed(self, form, name, value):
        form.fields.get(name)[0].value__set(value)
