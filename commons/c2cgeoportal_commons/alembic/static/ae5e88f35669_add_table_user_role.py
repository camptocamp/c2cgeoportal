# -*- coding: utf-8 -*-

# Copyright (c) 2018-2019, Camptocamp SA
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

"""Add table user_role and rename user.role_name to settings_role_id

Revision ID: ae5e88f35669
Revises: 53d671b17b20
Create Date: 2018-12-04 15:32:30.506633
"""

from alembic import op
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = 'ae5e88f35669'
down_revision = '53d671b17b20'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']
    staticschema = config['schema_static']

    op.create_table(
        'user_role',
        Column('user_id', Integer, ForeignKey(staticschema + '.user.id'), primary_key=True),
        Column('role_id', Integer, primary_key=True),
        schema=staticschema
    )
    op.execute(
        """
INSERT INTO "{staticschema}"."user_role" ("user_id", "role_id")
SELECT "user"."id", "role"."id"
FROM "{staticschema}"."user"
LEFT JOIN "{schema}"."role" ON "role"."name" = "user"."role_name";""".
        format(schema=schema, staticschema=staticschema)
    )

    op.add_column('user', Column('settings_role_id', Integer), schema=staticschema)
    op.execute(
        """
UPDATE "{staticschema}"."user"
SET "settings_role_id" = "role"."id"
FROM "{schema}"."role"
WHERE "role"."name" = "user"."role_name";""".
        format(schema=schema, staticschema=staticschema)
    )

    op.drop_column('user', 'role_name', schema=staticschema)


def downgrade():
    schema = config['schema']
    staticschema = config['schema_static']

    op.add_column('user', Column('role_name', Unicode), schema=staticschema)

    op.execute(
        """
UPDATE "{staticschema}"."user"
SET "role_name" = "role"."name"
FROM "{schema}"."role"
WHERE "role"."id" = "user"."settings_role_id";""".
        format(schema=schema, staticschema=staticschema)
    )

    op.drop_column('user', 'settings_role_id', schema=staticschema)

    op.drop_table('user_role', schema=staticschema)
