import unittest
import pytest
import transaction
import sqlahelper

from pyramid.config import Configurator
from pyramid import testing

from c2cgeoportal_commons.scripts.initializedb import init_db


def app(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    In our case, this is only used for tests.
    """
    config = Configurator(settings=settings)
    return config.make_wsgi_app()


@pytest.fixture(scope='module')
def dbsession(request):
    config = testing.setUp(settings={
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857
    })
    settings = config.get_settings()

    from c2cgeoportal_commons.models import (
        get_engine,
        get_session_factory,
        get_tm_session,
        generate_mappers,
        )

    generate_mappers(settings)

    engine = get_engine(settings)
    sqlahelper.add_engine(engine)

    init_db(engine, force=True)

    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)

    return session

@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertUsersTestData(dbsession):
    from c2cgeoportal_commons.models.main import User
    user = User("babar")
    transaction = dbsession.begin_nested()
    dbsession.add(user)

    yield

    transaction.rollback()

@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertRolesTestData(dbsession):
    from c2cgeoportal_commons.models.main import Role
    role = Role("secretaire")
    transaction = dbsession.begin_nested()
    dbsession.add(role)

    yield

    transaction.rollback()

@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def transact(request, dbsession):
    transaction = dbsession.begin_nested()

    yield

    transaction.rollback()

@pytest.mark.usefixtures("insertUsersTestData", "transact")
class TestUser():

    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        users = dbsession.query(User).all()
        assert len(users) == 1, "querying for users"
        assert users[0].username == 'babar', "user from test data is babar"

    def test_remove(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        users = dbsession.query(User).all()
        dbsession.delete(users[0])
        users = dbsession.query(User).all()
        assert len(users) == 0, "removed a user"

    def test_add(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        user = User("momo")
        dbsession.add(user)
        users = dbsession.query(User).all()
        assert len(users) == 2, "added a user"
        assert users[0].username == 'babar', "user from test data is babar"
        assert users[1].username == 'momo', "added user is momo"

    def test_no_role(self, dbsession):
        from c2cgeoportal_commons.models.main import Role
        users = dbsession.query(Role).all()
        assert len(users) == 0, "querying for role"


@pytest.mark.usefixtures("insertRolesTestData", "transact")
class TestRole():

    def test_no_user(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        users = dbsession.query(User).all()
        assert len(users) == 0, "querying for users"

    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.main import Role
        roles = dbsession.query(Role).all()
        assert len(roles) == 1, "querying for roles"
        assert roles[0].name == 'secretaire', "role from test data is secretaire"
