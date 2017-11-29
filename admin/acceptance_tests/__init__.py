import os
import pytest


def check_grid_headers(test_app, path, expected_col_headers, language='en'):
    res = test_app.get(path, status=200)
    res1 = res.click(verbose=True, href='language=' + language)

    res2 = res1.follow()

    effective_cols = [(th.attrs['data-column-id'], th.getText()) for th in res2.html.select('th')]
    assert expected_col_headers == effective_cols, \
        str.format('{} and {} differs.', str(expected_col_headers), str(effective_cols))
    commands = res2.html.select_one('th[data-column-id="_id_"]')
    assert 'false' == commands.attrs['data-searchable']
    assert 'false' == commands.attrs['data-sortable']
    assert 1 == len(list(filter(lambda x: str(x.contents) == "['New']",
                                res2.html.findAll('a'))))


skip_if_ci = pytest.mark.skipif(
    os.environ.get('CI', "false") == "true", reason="Not running on CI"
)
