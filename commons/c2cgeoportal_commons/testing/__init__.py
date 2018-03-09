from typing import Dict
import transaction
from transaction import TransactionManager

import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from c2cgeoportal_commons.testing import get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.config import config
from c2cgeoportal_commons.models import Base


def get_engine(settings: Dict, prefix: str='sqlalchemy.') -> Engine:
    return engine_from_config(settings, prefix)


def get_session_factory(engine: Engine) -> sessionmaker:
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory: sessionmaker, transaction_manager: TransactionManager) -> Session:
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)

    """
    dbsession = session_factory()
    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager)
    return dbsession


def init_db(connection: Connection, force: bool=False, test: bool=False) -> None:
    import c2cgeoportal_commons.models.main  # noqa: F401
    import c2cgeoportal_commons.models.static  # noqa: F401

    schema = config['schema']
    schema_static = config['schema_static']
    if force:
        if schema_exists(connection, schema):
            connection.execute('DROP SCHEMA {} CASCADE;'.format(schema))
        if schema_exists(connection, schema_static):
            connection.execute('DROP SCHEMA {} CASCADE;'.format(schema_static))

    if not schema_exists(connection, schema):
        connection.execute('CREATE SCHEMA "{}";'.format(schema))

    if not schema_exists(connection, schema_static):
        connection.execute('CREATE SCHEMA "{}";'.format(schema_static))

    Base.metadata.create_all(connection)

    session_factory = get_session_factory(connection)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        if test:
            setup_test_data(dbsession)


def schema_exists(connection: Connection, schema_name: str) -> bool:
    sql = """
SELECT count(*) AS count
FROM information_schema.schemata
WHERE schema_name = '{}';
""".format(schema_name)
    result = connection.execute(sql)
    row = result.first()
    return row[0] == 1


def setup_test_data(dbsession: Session) -> None:
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User
    role_admin = dbsession.merge(Role(name='role_admin'))
    role_user = dbsession.merge(Role(name='role_user'))

    dbsession.merge(User(
        username='admin',
        email='admin@camptocamp.com',
        role=role_admin
    ))
    dbsession.merge(User(
        username='user',
        email='user@camptocamp.com',
        role=role_user
    ))
