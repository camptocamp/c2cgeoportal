import os
import pytest
import re


def clean_form(form):
    clean_form = form.replace('\n', ' ')
    while re.search('  ', clean_form, re.MULTILINE):
        clean_form = clean_form.replace('  ', ' ')
    clean_form = clean_form.replace(' >', '>')
    return clean_form


skip_if_travis = pytest.mark.skipif(os.environ.get('TRAVIS', "false") == "true",
                                    reason="Not running on Travis")
