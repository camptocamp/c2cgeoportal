from c2cgeoportal_commons.tests import transact
from c2cgeoportal_commons.tests import raise_db_error_on_query

import pytest
import transaction
from c2cgeoportal_commons.scripts.initializedb import init_db
from c2cgeoportal_commons.models import get_engine, get_session_factory, get_tm_session, includeme
from pyramid.config import Configurator

config = Configurator(settings={
    'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
    'schema': 'main',
    'parent_schema': '',
    'srid': 3857
})

@pytest.fixture(scope='session')
def dbsession(request):
    settings = config.get_settings()
    config.include('c2cgeoportal_admin.routes')
    config.include('c2cgeoportal_commons.models')
    engine = get_engine(settings)
    init_db(engine, force=True)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    return session

@pytest.fixture(scope='session')
@pytest.mark.usefixtures("dbsession")
def app(request, dbsession):
    config.include('pyramid_jinja2')
    config.scan(package='c2cgeoportal_admin.views')
    from webtest import TestApp
    testapp = TestApp(config.make_wsgi_app())
    return testapp;
