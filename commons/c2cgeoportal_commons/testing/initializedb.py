import os
import sys
from typing import List

from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from c2cgeoportal_commons.models import Base


def usage(argv: List[str]) -> None:
    cmd = os.path.basename(argv[0])
    print("usage: %s <config_uri> [var=value]\n" '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def schema_exists(connection: Connection, schema_name: str) -> bool:
    sql = """
SELECT count(*) AS count
FROM information_schema.schemata
WHERE schema_name = '{}';
""".format(
        schema_name
    )
    result = connection.execute(sql)
    row = result.first()
    return row[0] == 1


def truncate_tables(connection: Connection) -> None:
    for t in Base.metadata.sorted_tables:
        connection.execute("TRUNCATE TABLE {}.{} CASCADE;".format(t.schema, t.name))


def setup_test_data(dbsession: Session) -> None:
    from c2cgeoportal_commons.models.main import Role  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.static import User  # pylint: disable=import-outside-toplevel

    role_admin = dbsession.merge(Role(name="role_admin"))
    role_user = dbsession.merge(Role(name="role_user"))

    dbsession.merge(
        User(username="admin", email="admin@camptocamp.com", settings_role=role_admin, roles=[role_admin])
    )
    dbsession.merge(
        User(username="user", email="user@camptocamp.com", settings_role=role_user, roles=[role_user])
    )
