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

"""Remove trigger on_role_name_change

Revision ID: 338b57593823
Revises: dba87f2647f9
Create Date: 2018-12-05 09:13:21.191424
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = '338b57593823'
down_revision = 'dba87f2647f9'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    op.execute('DROP TRIGGER on_role_name_change ON {schema}.role'.format(
        schema=schema
    ))
    op.execute('DROP FUNCTION {schema}.on_role_name_change()'.format(
        schema=schema
    ))


def downgrade():
    schema = config['schema']
    staticschema = config['schema_static']

    op.execute(
        """
CREATE OR REPLACE FUNCTION {schema}.on_role_name_change()
RETURNS trigger AS
$$
BEGIN
IF NEW.name <> OLD.name THEN
UPDATE {staticschema}."user" SET role_name = NEW.name WHERE role_name = OLD.name;
END IF;
RETURN NEW;
END;
$$
LANGUAGE plpgsql""".
        format(schema=schema, staticschema=staticschema)
    )
    op.execute(
        'CREATE TRIGGER on_role_name_change AFTER UPDATE ON {schema}.role FOR EACH ROW '
        'EXECUTE PROCEDURE {schema}.on_role_name_change()'.format(
            schema=schema
        )
    )
