import pytest
from pyramid import testing
from pyramid.view import view_config
from webtest import TestApp
from wsgiref.simple_server import make_server
import threading

from c2cgeoportal_commons.tests import (  # noqa: F401
    dbsession,
    transact,
    raise_db_error_on_query,
)


@pytest.fixture(scope='session')
def settings(request):
    return {
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857,
        'pyramid.available_languages': 'fr en'
    }


def prepare_app(dbsession, settings):  # noqa: F811
    config = testing.setUp(settings=settings)
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.include('c2cgeoportal_admin.routes')
    config.include('c2cgeoportal_commons.models')
    config.scan(package='c2cgeoportal_admin.views')

    config.add_route('user_add', 'user_add')
    config.add_route('users_nb', 'users_nb')
    config.scan(package='acceptance_tests')
    config.add_request_method(lambda request: dbsession, 'dbsession', reify=True)

    app = config.make_wsgi_app()
    return app


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("dbsession")
def test_app(request, dbsession, settings):
    app = prepare_app(dbsession, settings)
    testapp = TestApp(app)
    return testapp


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("dbsession")
def selenium_app(request, dbsession, settings):
    app = prepare_app(dbsession, settings)
    srv = make_server('', 6543, app)
    threading.Thread(target=srv.serve_forever).start()
    yield()
    srv.shutdown()


@view_config(route_name='user_add', renderer='./learn_test.jinja2')
def view_committing_user(request):
    from c2cgeoportal_commons.models.main import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}


@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.main import User
    users = request.dbsession.query(User).all()
    username = 'None'
    if len(users) > 0:
        username = users[0].username
    return {'size': len(users), 'first': username, 'project': 'c2cgeoportal_admin'}
