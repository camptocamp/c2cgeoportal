import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..meta import Base
from .. import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)

    with engine.begin() as connection:
        init_db(connection)

    '''
    # generate the Alembic version table and stamp it with the latest revision
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_section_option(
        'alembic', 'sqlalchemy.url', engine.url.__str__())
    command.stamp(alembic_cfg, 'head')
    '''


def init_db(connection):
    from .. import main
    from .. import schema

    if not schema_exists(connection, schema):
        connection.execute("CREATE SCHEMA \"{}\";".format(schema))

    schema_static = "{}_static".format(schema)
    if not schema_exists(connection, schema_static):
        connection.execute("CREATE SCHEMA \"{}\";".format(schema_static))

    Base.metadata.create_all(connection)

    session_factory = get_session_factory(connection)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        '''
        model = MyModel(name='one', value=1)
        dbsession.add(model)'''


def schema_exists(connection, schema_name):
    sql = '''
SELECT count(*) AS count
FROM information_schema.schemata
WHERE schema_name = '{}';
'''.format(schema_name)
    result = connection.execute(sql)
    row = result.first()
    return row[0] == 1
