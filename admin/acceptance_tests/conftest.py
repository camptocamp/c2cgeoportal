from c2cgeoportal_commons.tests import dbsession, transact, raise_db_error_on_query

import pytest
import transaction
from c2cgeoportal_commons.scripts.initializedb import init_db
from c2cgeoportal_commons.models import get_engine, get_session_factory, get_tm_session, generate_mappers
from pyramid.config import Configurator

config = Configurator(settings={
    'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
    'schema': 'main',
    'parent_schema': '',
    'srid': 3857
})

@pytest.fixture(scope='session')
@pytest.mark.usefixtures("dbsession")
def app(request, dbsession):
    config.include('pyramid_jinja2')
    config.add_route('test', 'test/')
    config.include('c2cgeoportal_admin.routes')
    config.include('c2cgeoportal_commons.models')
    config.scan(package='c2cgeoportal_admin.views')
    config.scan(package='acceptance_tests')
    from webtest import TestApp
    config.add_request_method(lambda r: dbsession, 'dbsession', reify=True)
    testapp = TestApp(config.make_wsgi_app())
    return testapp;

from pyramid.view import view_config

@view_config(route_name='test', renderer='./test.jinja2')
def view_commiting_user(request):
    from c2cgeoportal_commons.models.main import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}
