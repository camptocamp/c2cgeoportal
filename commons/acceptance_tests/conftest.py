import pytest

from c2cgeoportal_commons.tests import dbsession  # noqa: F401
from c2cgeoportal_commons.tests import transact  # noqa: F401


@pytest.fixture(scope='session')
def settings():
    return {
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857
    }
