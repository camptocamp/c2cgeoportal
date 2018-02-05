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

    def _check_interfaces(self, form, interfaces, item):
        self.check_checkboxes(
            form,
            'interfaces',
            [{
                'label': i.name,
                'value': str(i.id),
                'checked': i in item.interfaces
            } for i in sorted(interfaces, key=lambda i: i.name)])

    def _check_restrictionsareas(self, form, ras, item):
        self.check_checkboxes(
            form,
            'restrictionareas',
            [{
                'label': ra.name,
                'value': str(ra.id),
                'checked': ra in item.restrictionareas
            } for ra in sorted(ras, key=lambda ra: ra.name)])

    def get_first_field_named(self, form, name):
        return form.fields.get(name)[0]

    def set_first_field_named(self, form, name, value):
        form.fields.get(name)[0].value__set(value)

    def _check_sequence(self, sequence, expected):
        seq_items = sequence.select('.deform-seq-item')
        assert len(expected) == len(seq_items)
        for seq_item, exp in zip(seq_items, expected):
            self._check_mapping(seq_item, exp)

    def _check_mapping(self, mapping_item, expected):
        for exp in expected:
            input_tag = mapping_item.select_one('[name="{}"]'.format(exp['name']))
            if 'value' in exp:
                if input_tag.name == 'select':
                    self._check_select(input_tag, exp['value'])
                elif input_tag.name == 'textarea':
                    assert (exp['value'] or '') == (input_tag.string or '')
                else:
                    assert (exp['value'] or '') == input_tag.attrs.get('value', '')
            if exp.get('hidden', False):
                assert 'hidden' == input_tag['type']
            if 'label' in exp:
                label_tag = mapping_item.select_one('label[for="{}"]'.format(input_tag['id']))
                assert exp['label'] == label_tag.getText().strip()

    def _check_select(self, select, expected):
        for exp, option in zip(expected, select.find_all('option')):
            if 'text' in exp:
                assert exp['text'] == option.text
            if 'value' in exp:
                assert exp['value'] == option['value']
            if 'selected' in exp:
                assert exp['selected'] == ('selected' in option.attrs)

    @staticmethod
    def check_one_submission_problem(expected_msg, resp):
        assert 'There was a problem with your submission' == \
            resp.html.select_one('div[class="error-msg-lbl"]').text
        assert 'Errors have been highlighted below' == \
            resp.html.select_one('div[class="error-msg-detail"]').text
        assert expected_msg == \
            resp.html.select_one("[class~'has-error']").select_one("[class~'help-block']").getText()
