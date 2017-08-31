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


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def transact(request, dbsession):
    transaction = dbsession.begin_nested()

    yield

    transaction.rollback()
