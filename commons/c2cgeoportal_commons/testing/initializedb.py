# -*- coding: utf-8 -*-

# Copyright (c) 2017-2020, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


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
