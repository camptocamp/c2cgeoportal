import pytest
from pyramid import testing

from c2cgeoportal_commons.tests import dbsession, transact, raise_db_error_on_query

@pytest.fixture(scope='session')
def settings(request):
    return {
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857
    }

@pytest.fixture(scope='session')
@pytest.mark.usefixtures("dbsession")
def app(request, dbsession, settings):
    config = testing.setUp(settings=settings)
    config.include('pyramid_jinja2')
    config.add_route('test', 'test')
    config.add_route('users_nb', 'users_nb')
    config.include('c2cgeoportal_admin.routes')
    config.include('c2cgeoportal_commons.models')
    config.scan(package='c2cgeoportal_admin.views')
    config.scan(package='acceptance_tests')
    from webtest import TestApp
    config.add_request_method(lambda r: dbsession, 'dbsession', reify=True)
    testapp = TestApp(config.make_wsgi_app())
    return testapp;

from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.exc import DBAPIError

@view_config(route_name='test', renderer='./learn_test.jinja2')
def view_commiting_user(request):
    from c2cgeoportal_commons.models.main import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}

@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    try:
        from c2cgeoportal_commons.models.main import User
        users = request.dbsession.query(User).all();
        username = 'None'
        if len(users) > 0:
            username = users[0].username
        return {'size': len(users), 'first': username, 'project': 'c2cgeoportal_admin'}

    except DBAPIError:
        return Response("""ERROR FOR TEST""", content_type='text/plain', status=500)