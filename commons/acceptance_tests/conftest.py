import pytest
from c2cgeoportal_commons.tests import dbsession
from c2cgeoportal_commons.tests import transact

@pytest.fixture(scope='session')
def settings(request):
    return {
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857
    }

