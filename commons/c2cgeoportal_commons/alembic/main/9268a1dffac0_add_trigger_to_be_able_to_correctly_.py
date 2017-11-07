# -*- coding: utf-8 -*-

# Copyright (c) 2017, Camptocamp SA
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

"""Add trigger to be able to correctly change the role name

Revision ID: 9268a1dffac0
Revises: 32b21aa1d0ed
Create Date: 2017-01-11 11:07:53.042003
"""

from alembic import op, context

# revision identifiers, used by Alembic.
revision = '9268a1dffac0'
down_revision = '32b21aa1d0ed'
branch_labels = None
depends_on = None


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.execute("""
CREATE OR REPLACE FUNCTION {schema}.on_role_name_change()
RETURNS trigger AS
$$
BEGIN
IF NEW.name <> OLD.name THEN
UPDATE {schema}."user" SET role_name = NEW.name WHERE role_name = OLD.name;
END IF;
RETURN NEW;
END;
$$
LANGUAGE plpgsql""".format(schema=schema))

    op.execute(
        'CREATE TRIGGER on_role_name_change AFTER UPDATE ON {schema}.role FOR EACH ROW '
        'EXECUTE PROCEDURE {schema}.on_role_name_change()'.format(
            schema=schema
        )
    )


def downgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.execute('DROP TRIGGER on_role_name_change ON {schema}.role'.format(
        schema=schema
    ))
    op.execute('DROP FUNCTION {schema}.on_role_name_change()'.format(
        schema=schema
    ))
