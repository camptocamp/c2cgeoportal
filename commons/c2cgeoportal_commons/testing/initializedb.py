import os
import sys
from typing import List

import transaction
from logging.config import fileConfig

from pyramid.paster import get_appsettings

from pyramid.scripts.common import parse_vars
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from alembic import command, config as alembic_config

from c2cgeoportal_commons.models import (
    Base,
)
from c2cgeoportal_commons.testing import get_engine, get_session_factory, get_tm_session, generate_mappers
from c2cgeoportal_commons.config import config


def usage(argv: List[str]) -> None:
    cmd = os.path.basename(argv[0])
    print(
        'usage: %s <config_uri> [var=value]\n'
        '(example: "%s development.ini")' % (cmd, cmd)
    )
    sys.exit(1)


def main(argv: List[str]=sys.argv) -> None:
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])

    fileConfig(config_uri, defaults=dict(os.environ))
    options.update(os.environ)
    settings = get_appsettings(config_uri, options=options)
    generate_mappers()

    engine = get_engine(settings)

    with engine.begin() as connection:
        init_db(
            connection,
            force='--force' in options,
            test='--test' in options
        )


def init_db(connection: Connection, alembic_ini: str=None, force: bool=False, test: bool=False) -> None:
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

    if alembic_ini is None:
        Base.metadata.create_all(connection)
    else:
        def upgrade(schema: str) -> None:
            cfg = alembic_config.Config(alembic_ini, ini_section=schema)
            cfg.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation
            command.upgrade(cfg, 'head')
        upgrade('main')
        upgrade('static')

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


def truncate_tables(connection: Connection) -> None:
    for t in Base.metadata.sorted_tables:
        connection.execute('TRUNCATE TABLE {}.{} CASCADE;'.format(t.schema, t.name))


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
