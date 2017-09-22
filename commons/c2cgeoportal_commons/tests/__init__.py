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


class BaseTest(unittest.TestCase):
    def setUp(self):
        '''
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:'
        })
        self.config.include('.models')
        settings = self.config.get_settings()

        from .models import (
            get_engine,
            get_session_factory,
            get_tm_session,
            )

        self.engine = get_engine(settings)
        session_factory = get_session_factory(self.engine)

        self.session = get_tm_session(session_factory, transaction.manager)
        '''

    def init_database(self):
        from .models.meta import Base
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        '''
        from .models.meta import Base

        testing.tearDown()
        transaction.abort()
        Base.metadata.drop_all(self.engine)
        '''


def test_import(dbsession):
    from c2cgeoportal_commons.models import main


@pytest.mark.usefixtures("dbsession")
class TestUser():

    def test_all_users(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        dbsession.query(User).all()
